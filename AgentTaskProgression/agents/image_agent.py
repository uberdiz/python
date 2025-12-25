"""
Image Recognition Agent - Analyzes UI mockups and screenshots
Uses HuggingFace Vision Models (Qwen 2.5-VL, Llama 3.2 Vision, etc.)
"""
from core.base_agent import BaseAgent
import base64
import os
import io

class ImageAgent(BaseAgent):
    """Agent for image/mockup analysis"""
    
    def __init__(self, name="image_agent", role="Image Analyzer", model_provider="huggingface", model_name="llama3.2-vision", orchestrator=None):
        super().__init__(name, role, model_provider, model_name, orchestrator)
        
    def process(self, task_input):
        """Main entry point for image analysis tasks"""
        # Handle both dict and string input
        if isinstance(task_input, dict):
            message = task_input.get("message", "")
            image_paths = task_input.get("image_paths", [])
            # Support single image_path as well
            image_path = task_input.get("image_path")
            if image_path and image_path not in image_paths:
                image_paths.insert(0, image_path)
            
            ref_path = task_input.get("reference_image", self._extract_reference_path(message))
            conversation_history = task_input.get("conversation_history", [])
        else:
            # If it's a string, we probably don't have the image paths here.
            # This case shouldn't normally happen for ImageAgent but let's be safe.
            message = task_input
            image_paths = []
            ref_path = self._extract_reference_path(message)
            conversation_history = []

        if not image_paths:
            return "No image paths provided for analysis."
            
        # Analyze the images
        results = []
        for path in image_paths:
            if os.path.exists(path):
                try:
                    analysis = self.analyze_image(path, ref_path, message, conversation_history)
                    results.append(analysis)
                except Exception as e:
                    return f"Error analyzing image at {path}: {e}"
        
        combined_analysis = "\n\n---\n\n".join(results)
        
        # Format message for next agent with full context
        routing_message = f"IMAGE_ANALYSIS_COMPLETE\n\nOriginal User Request: {message}\n\n[TASK_SUMMARY]\nAnalyze the provided image(s) and apply the following UI/UX changes to the project:\n{combined_analysis}\n[/TASK_SUMMARY]"
        
        # Send to Reviser if available, otherwise Planner
        if self.orchestrator:
            # Check if we should feed back into the main app pipeline for advanced modification
            if hasattr(self.orchestrator, 'app') and self.orchestrator.app:
                app = self.orchestrator.app
                # If there's a project path, we likely want the full 6-phase pipeline
                if hasattr(app, 'project_path') and app.project_path:
                    self.log("Triggering advanced modification pipeline via app.process_chat_message...")
                    # Delay slightly to ensure image analysis result is displayed first
                    app.root.after(1000, lambda: app.process_chat_message(routing_message, conversation_history=conversation_history))
                    return combined_analysis

            reviser = self.orchestrator.find_agent_by_role("Reviser")
            planner = self.orchestrator.find_agent_by_role("Planner")
            
            if reviser:
                self.send_message(reviser, routing_message)
            elif planner:
                self.send_message(planner, routing_message)
            
        return combined_analysis
        
    def analyze_image(self, image_path, ref_path=None, task_context="", conversation_history=None):
        try:
            from core.vision import VisionProcessor
            vp = VisionProcessor(getattr(self.orchestrator.app, 'root', None) if self.orchestrator and hasattr(self.orchestrator, 'app') else None)
            img = vp.load_image(image_path)
            
            summary = []
            
            # 1. Basic Image Analysis (Palette, OCR, Size)
            if img:
                info = vp.analyze(img)
                size = info.get("size", {})
                summary.append(f"### Image Properties")
                summary.append(f"- **Size**: {size.get('w','?')}x{size.get('h','?')}")
                
                palette = info.get("palette", [])
                if palette:
                    cols = ", ".join([f"rgb({c['rgb'][0]},{c['rgb'][1]},{c['rgb'][2]})" for c in palette[:6]])
                    summary.append(f"- **Primary Colors**: {cols}")
                
                ocr = info.get("ocr_text", "")
                if ocr and ocr.strip():
                    summary.append(f"- **Detected Text**: {ocr.strip()[:500]}")

            # 2. Reference Image Matching (if provided)
            if ref_path and os.path.exists(ref_path):
                ref_img = vp.load_image(ref_path)
                if img and ref_img:
                    matches = vp.match_template(img, ref_img)
                    if matches:
                        best = matches[0]
                        summary.append(f"### Reference Match")
                        summary.append(f"- Found reference image at x={best['x']}, y={best['y']} (Score: {best['score']:.2f})")
                        summary.append(f"- Similarity: {'High' if best['score'] < 5.0 else 'Moderate' if best['score'] < 12.0 else 'Low'}")

            # 3. VLM Analysis (Detailed description)
            # Use resized image for VLM to save tokens
            resized_img = vp.resize_for_vlm(img)
            if resized_img:
                # Save to temporary bytes for base64 encoding
                buffer = io.BytesIO()
                resized_img.save(buffer, format="PNG")
                image_data = base64.b64encode(buffer.getvalue()).decode("utf-8")
            else:
                # Fallback to original if resize failed
                with open(image_path, "rb") as f:
                    image_data = base64.b64encode(f.read()).decode("utf-8")
            
            ext = os.path.splitext(image_path)[1].lower()
            mime_type = {
                ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                ".gif": "image/gif", ".webp": "image/webp"
            }.get(ext, "image/png")
            
            vlm_prompt = f"""Task: {task_context if task_context else 'Analyze UI.'}
            Provide a concise technical analysis for a developer to implement this:
            1. Layout & Components: Identify key UI elements and their arrangement.
            2. Styling: Note colors, fonts, and overall theme.
            3. Functionality: Infer intended behavior from visual cues.
            
            SUMMARY_FOR_PLANNER: A one-sentence technical directive for a coding agent to execute this task.
            Be concise and professional."""

            vlm_result = self._call_vision_model(image_data, mime_type, vlm_prompt, conversation_history, image_path=image_path)
            summary.append(f"\n### AI Interpretation\n{vlm_result}")
            
            return "\n".join(summary)
            
        except Exception as e:
            self.log(f"Image analysis error: {e}")
            return f"Error analyzing image: {e}"
            
    def _call_vision_model(self, image_base64, mime_type, prompt, conversation_history=None, image_path=None):
        """Call vision model with image and custom prompt (Supports HF, Ollama, OpenAI, Gemini)"""
        try:
            # 1. Handle Ollama specifically if it's the provider
            if self.model_provider == "ollama":
                try:
                    import ollama
                    # Use the library as requested by user
                    messages = []
                    if conversation_history:
                        for item in conversation_history:
                            # Only add text content to history for vision models to keep it clean
                            if isinstance(item.get("content"), str):
                                messages.append({"role": item["role"], "content": item["content"]})
                    
                    # Add current message with image
                    user_content = prompt
                    msg = {
                        "role": "user",
                        "content": user_content
                    }
                    
                    # Prefer resized base64 data to save tokens and processing time
                    images = []
                    if image_base64:
                        images.append(image_base64)
                    elif image_path and os.path.exists(image_path):
                        images.append(image_path)
                    
                    if images:
                        msg["images"] = images
                    
                    messages.append(msg)
                    
                    self.log(f"Calling Ollama vision with model: {self.model_name}")
                    resp = ollama.chat(model=self.model_name, messages=messages)
                    return resp.get("message", {}).get("content", "")
                except Exception as e:
                    self.log(f"Ollama library call failed, falling back to API: {e}")
                    # Fallback to core.llm if library fails
                    from core.llm import call_llm
                    return call_llm(prompt, "http://localhost:11434", self.model_name, "ollama", images=[image_base64])

            # 2. Handle OpenAI/Gemini/Anthropic via core.llm if they are the provider
            if self.model_provider in ["openai", "google", "anthropic"]:
                from core.llm import call_llm
                api_url, _, token, _ = self.orchestrator.app.ai_manager.get_provider_config(self.model_provider)
                return call_llm(prompt, api_url, self.model_name, self.model_provider, token, images=[image_base64])

            # 3. Default to HuggingFace (Existing implementation)
            from huggingface_hub import InferenceClient
            
            # Prepare messages for the VLM
            messages = []
            if conversation_history:
                for item in conversation_history:
                    messages.append({"role": item["role"], "content": item["content"]})
            
            # Add the current image analysis prompt
            messages.append(
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_base64}"}}
                    ]
                }
            )

            # Try InferenceClient with provider
            try:
                client = InferenceClient(
                    provider="together",
                    api_key=self._get_hf_token()
                )
                
                response = client.chat.completions.create(
                    model=self.model_name,
                    messages=messages
                )
                return response.choices[0].message.content
                
            except Exception as e:
                self.log(f"Provider failed, trying serverless: {e}")
                # Fallback to serverless
                client = InferenceClient(api_key=self._get_hf_token())
                
                response = client.chat.completions.create(
                    model=self.model_name,
                    messages=messages
                )
                return response.choices[0].message.content
                
        except ImportError:
            return "Required libraries not installed (huggingface_hub or ollama)."
        except Exception as e:
            return f"Vision model error: {e}"
            
    def _extract_image_path(self, task):
        """Extract main image path from task string"""
        import re
        # Look for path that ISN'T labeled as reference
        patterns = [
            r'(?:path|image):\s*([^\s,]+)',
            r'([A-Za-z]:\\[^"<>|\r\n]+\.(png|jpg|jpeg|gif|webp))',
            r'(/[^"<>|\r\n]+\.(png|jpg|jpeg|gif|webp))'
        ]
        for pattern in patterns:
            match = re.search(pattern, task, re.IGNORECASE)
            if match:
                path = match.group(1).strip()
                if "reference" not in task.lower() or path not in task.lower().split("reference")[1]:
                    return path
        return None

    def _extract_reference_path(self, task):
        """Extract reference image path from task string"""
        import re
        patterns = [
            r'reference(?: image)?:\s*([^\s,]+)',
            r'ref:\s*([^\s,]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, task, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

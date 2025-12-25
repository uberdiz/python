"""
Image Recognition Agent - Analyzes UI mockups and screenshots
Uses HuggingFace Vision Models (Qwen 2.5-VL, Llama 3.2 Vision, etc.)
"""
from core.base_agent import BaseAgent
import base64
import os

class ImageAgent(BaseAgent):
    """Agent for image/mockup analysis"""
    
    def __init__(self, name="image_agent", role="Image Analyzer", model_provider="huggingface", model_name="Qwen/Qwen2.5-VL-7B-Instruct", orchestrator=None):
        super().__init__(name, role, model_provider, model_name, orchestrator)
        
    def process(self, task_data):
        """Process image analysis task"""
        # Extract image path and optional reference image path from task_data
        image_path = task_data.get("image_path")
        message = task_data.get("message", "")
        conversation_history = task_data.get("conversation_history")
        ref_path = self._extract_reference_path(message)
        
        if not image_path or not os.path.exists(image_path):
            return "No valid image path provided."
            
        # Analyze the image
        analysis = self.analyze_image(image_path, ref_path, message, conversation_history)
        
        # Send to GUI coder if available
        if self.orchestrator and "gui_coder" in self.orchestrator.agents:
            self.send_message("gui_coder", f"IMAGE_ANALYSIS:\n{analysis}")
            
        return analysis
        
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
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
            
            ext = os.path.splitext(image_path)[1].lower()
            mime_type = {
                ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                ".gif": "image/gif", ".webp": "image/webp"
            }.get(ext, "image/png")
            
            vlm_prompt = f"""Task: {task_context if task_context else 'Analyze this UI mockup/screenshot.'}

Please provide a detailed technical analysis of this image:
1. Layout structure and hierarchy.
2. UI components (buttons, inputs, lists, cards, etc.) and their approximate positions.
3. Visual styling (colors, borders, shadows, fonts).
4. Functional interpretation (what does this UI likely do?).
5. If this is a mockup, suggest a technical implementation strategy (e.g., React, Tkinter, HTML/CSS).

Be extremely precise and detailed."""

            vlm_result = self._call_vision_model(image_data, mime_type, vlm_prompt, conversation_history)
            summary.append(f"\n### AI Interpretation\n{vlm_result}")
            
            return "\n".join(summary)
            
        except Exception as e:
            self.log(f"Image analysis error: {e}")
            return f"Error analyzing image: {e}"
            
    def _call_vision_model(self, image_base64, mime_type, prompt, conversation_history=None):
        """Call vision model with image and custom prompt"""
        try:
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
            return "huggingface_hub not installed."
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

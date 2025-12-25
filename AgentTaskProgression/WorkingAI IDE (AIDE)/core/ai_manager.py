"""
AI Manager - Centralized handling of AI providers and interactions
"""
import requests
import json
from core.llm import call_llm, test_llm_connection

class AIManager:
    def __init__(self, app):
        self.app = app
        self.default_providers = {
            "openai": {"name": "OpenAI API", "type": "openai", "url": "https://api.openai.com/v1/chat/completions", "model": "gpt-4o"},
            "deepseek": {"name": "DeepSeek API", "type": "openai", "url": "https://api.deepseek.com/v1/chat/completions", "model": "deepseek-chat"},
            "ollama": {"name": "Ollama (Local)", "type": "ollama", "url": "http://localhost:11434", "model": "codellama"},
            "huggingface": {"name": "HuggingFace API", "type": "huggingface", "url": "https://router.huggingface.co/hf-inference/v1/chat/completions", "model": "Qwen/Qwen2.5-7B-Instruct"},
            "anthropic": {"name": "Anthropic Claude", "type": "anthropic", "url": "https://api.anthropic.com/v1/messages", "model": "claude-3-5-sonnet-latest"},
            "google": {"name": "Google Gemini", "type": "google", "url": "https://generativelanguage.googleapis.com/v1/models", "model": "gemini-1.5-flash"}
        }
        self.usage_logs = []
        self._load_usage_logs()

    def get_providers(self):
        """Get all providers (defaults + custom)"""
        providers = self.default_providers.copy()
        custom_providers = self.app.settings.get("custom_providers", {})
        providers.update(custom_providers)
        return providers

    def add_custom_provider(self, provider_id, config):
        """Add or update a custom provider"""
        custom_providers = self.app.settings.get("custom_providers", {})
        custom_providers[provider_id] = config
        self.app.settings["custom_providers"] = custom_providers
        # Save handled by caller or via app.save_settings

    def delete_custom_provider(self, provider_id):
        """Remove a custom provider"""
        custom_providers = self.app.settings.get("custom_providers", {})
        if provider_id in custom_providers:
            del custom_providers[provider_id]
            self.app.settings["custom_providers"] = custom_providers
            # Save handled by caller or via app.save_settings

    def _load_usage_logs(self):
        """Load usage logs from a file or settings"""
        try:
            import os
            from app import SETTINGS_PATH
            log_path = os.path.join(os.path.dirname(SETTINGS_PATH), "usage_logs.json")
            if os.path.exists(log_path):
                with open(log_path, 'r') as f:
                    self.usage_logs = json.load(f)
        except Exception:
            self.usage_logs = []

    def _save_usage_logs(self):
        """Save usage logs to a file"""
        try:
            import os
            from app import SETTINGS_PATH
            log_path = os.path.join(os.path.dirname(SETTINGS_PATH), "usage_logs.json")
            with open(log_path, 'w') as f:
                json.dump(self.usage_logs[-1000:], f) # Keep last 1000 logs
        except Exception:
            pass

    def log_usage(self, provider, model, tokens_used=0):
        """Log API usage"""
        from datetime import datetime
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "provider": provider,
            "model": model,
            "tokens": tokens_used
        }
        self.usage_logs.append(log_entry)
        self._save_usage_logs()

    def get_active_provider(self):
        """Get primary active provider ID"""
        active = self.get_active_providers()
        return active[0] if active else "openai"

    def get_active_providers(self):
        """Get list of all active provider IDs"""
        active = self.app.settings.get("active_providers", [])
        if not active:
            # Fallback to legacy single provider setting
            legacy = self.app.settings.get("api_provider", "openai")
            return [legacy]
        return active

    def set_provider(self, provider_id, active=True, allow_multiple=None):
        """Activate or deactivate a provider"""
        providers = self.get_providers()
        if provider_id not in providers:
            raise ValueError(f"Provider {provider_id} does not exist")
            
        if allow_multiple is None:
            allow_multiple = self.app.settings.get("allow_multiple_providers", False)
            
        current_active = set(self.get_active_providers())
        
        if active:
            if not allow_multiple:
                current_active = {provider_id}
            else:
                current_active.add(provider_id)
        else:
            if provider_id in current_active:
                current_active.remove(provider_id)
            if not current_active:
                # Ensure at least one provider is active (default to openai)
                current_active = {"openai"}
        
        active_list = sorted(list(current_active))
        self.app.settings["active_providers"] = active_list
        # Primary provider for legacy code
        if active_list:
            self.app.settings["api_provider"] = active_list[0]
            
        if hasattr(self, "client"):
            delattr(self, "client")
            
        self.log_usage("provider_switch", {"active_providers": active_list})
        self.app.save_settings(self.app.settings)

    def get_provider_config(self, provider_id=None):
        """Get configuration for specific or current provider"""
        if not provider_id:
            provider_id = self.get_active_provider()
            
        providers = self.get_providers()
        config = providers.get(provider_id, self.default_providers.get("openai"))
        
        provider_type = config.get("type", "openai")
        settings = self.app.settings
        
        url = config.get("url", "")
        model = config.get("model", "")
        token = ""
        
        def _decrypt(val):
            try:
                import ctypes, base64
                if not val or not isinstance(val, str) or not val.startswith("enc:"):
                    return val or ""
                raw = base64.b64decode(val[4:])
                class DATA_BLOB(ctypes.Structure):
                    _fields_ = [("cbData", ctypes.c_uint), ("pbData", ctypes.c_void_p)]
                in_blob = DATA_BLOB(len(raw), ctypes.cast(ctypes.create_string_buffer(raw), ctypes.c_void_p))
                out_blob = DATA_BLOB()
                CryptUnprotectData = ctypes.windll.crypt32.CryptUnprotectData
                if CryptUnprotectData(ctypes.byref(in_blob), None, None, None, None, 0, ctypes.byref(out_blob)):
                    try:
                        buf = ctypes.string_at(out_blob.pbData, out_blob.cbData)
                        return buf.decode('utf-8')
                    finally:
                        ctypes.windll.kernel32.LocalFree(out_blob.pbData)
            except Exception:
                pass
            return val or ""

        # Tokens are stored in settings by provider_id
        token = _decrypt(settings.get(f"{provider_id}_key", ""))
        
        # If no specific key for this provider_id, try type-based key for defaults
        if not token and provider_id in self.default_providers:
            token = _decrypt(settings.get(f"{provider_type}_key", ""))

        return url, model, token, provider_type

    def test_connection(self, provider_id):
        """Test connection implementation"""
        url, model, token, provider_type = self.get_provider_config(provider_id)
        return test_llm_connection(provider_type, url, model, token)

    def generate_response(self, prompt, context=None, **params):
        """Generate response using active provider"""
        provider_id = self.get_active_provider()
        url, model, token, provider_type = self.get_provider_config(provider_id)
        
        # Here we could inject context into the prompt if not already handled
        full_prompt = prompt
        if context:
            # Simple context injection if needed, but usually agents handle this
            pass
        
        # Allow UI to pass model parameters (temperature, max_tokens, system_prompt)
        temperature = params.get("temperature", self.app.settings.get("temperature", 0.7))
        max_tokens = params.get("max_tokens", self.app.settings.get("max_tokens", 2000))
        system_prompt = params.get("system_prompt", self.app.settings.get("system_prompt", "You are a helpful AI coding assistant. Provide clear, concise code and explanations."))

        response = call_llm(full_prompt, url, model, provider_type, token, temperature=temperature, max_tokens=max_tokens, system_prompt=system_prompt)
        
        # Log usage (tokens estimation if not provided by response)
        # Note: In a real app, we'd get actual token counts from the API response
        tokens_estimate = len(full_prompt.split()) + len(response.split())
        self.log_usage(provider_id, model, tokens_estimate)
        
        return response

    def summarize_project(self, project_path):
        """Generate a token-efficient summary of the project"""
        import os
        if not project_path or not os.path.exists(project_path):
            return "No project path provided."
            
        summary = [f"# Project Summary: {os.path.basename(project_path)}", ""]
        
        # Walk through files
        for root, dirs, files in os.walk(project_path):
            # Ignore common garbage
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'venv', 'env', 'node_modules', '.idea', '.vscode']]
            
            for file in files:
                if file.endswith(('.pyc', '.git', '.png', '.jpg', '.ico', '.dll', '.so')):
                    continue
                    
                path = os.path.join(root, file)
                rel_path = os.path.relpath(path, project_path)
                
                try:
                    summary.append(f"## File: {rel_path}")
                    
                    # Read content but truncate/summarize
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        
                    # Custom simple summarizer: get classes and functions
                    has_defs = False
                    for line in lines:
                        strip = line.strip()
                        if strip.startswith(("class ", "def ", "import ", "from ")):
                            summary.append(f"  {strip}")
                            has_defs = True
                        elif strip.startswith("#"): # Include comments? Maybe too noisy
                            pass
                            
                    if not has_defs:
                        # If no code structure, just say "Empty or resource file" or show first few lines
                        if len(lines) > 0:
                            summary.append(f"  (Content: {len(lines)} lines)")
                        else:
                            summary.append("  (Empty)")
                    
                    summary.append("") # Spacer
                        
                except Exception:
                    summary.append(f"  (Error reading file)")
        
        return "\n".join(summary)

    def get_allowed_models(self, provider=None):
        """Get list of allowed models from settings, optionally filtered by provider"""
        # 1. Try to get cached models first if provider specified
        if provider:
            cached = self.app.settings.get(f"cached_models_{provider}", [])
            if cached:
                return cached

        # 2. Fallback to provider defaults if specified, BEFORE checking global whitelist
        # This ensures new agents for a provider aren't blocked by a stale whitelist
        defaults = {
            "openai": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
            "anthropic": ["claude-3-5-sonnet-latest", "claude-3-5-haiku-latest", "claude-3-opus-20240229"],
            "google": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.0-pro"],
            "ollama": ["llama3", "codellama", "mistral", "deepseek-coder-v2", "llava"],
            "huggingface": ["Qwen/Qwen2.5-7B-Instruct", "meta-llama/Llama-3.2-11B-Vision-Instruct"],
            "deepseek": ["deepseek-chat", "deepseek-coder"],
            "mistral": ["mistral-large-latest", "mistral-small-latest"],
            "groq": ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
        }
        
        # 3. Check for global whitelist
        allowed_str = self.app.settings.get("allowed_models", "")
        if allowed_str:
            all_allowed = [m.strip() for m in allowed_str.split(",") if m.strip()]
            
            if provider:
                # If provider is specified, filter the whitelist
                provider_map = {
                    "openai": ["gpt-", "text-davinci", "o1-"],
                    "anthropic": ["claude-"],
                    "google": ["gemini-"],
                    "ollama": [], 
                    "huggingface": ["/"], 
                    "deepseek": ["deepseek-"],
                    "mistral": ["mistral-", "mixtral-"],
                    "groq": ["llama-", "mixtral-", "gemma-"]
                }
                prefixes = provider_map.get(provider, [])
                if prefixes:
                    filtered = [m for m in all_allowed if any(m.lower().startswith(p) or p in m.lower() for p in prefixes)]
                    if filtered: return filtered
                elif provider == "ollama":
                    cloud_prefixes = ["gpt-", "claude-", "gemini-"]
                    filtered = [m for m in all_allowed if not any(m.lower().startswith(p) for p in cloud_prefixes)]
                    if filtered: return filtered
                
                # If no matches in whitelist for this provider, use its defaults
                if provider in defaults:
                    return defaults[provider]
            
            return all_allowed

        # 4. Fallback defaults
        if provider in defaults:
            return defaults[provider]
        
        # Return all defaults if no provider specified
        all_defaults = []
        for v in defaults.values(): all_defaults.extend(v)
        return list(set(all_defaults))

    def fetch_available_models(self, provider_id):
        """Programmatically fetch models for a provider"""
        url, _, token, provider_type = self.get_provider_config(provider_id)
        
        try:
            if provider_type == "openai" or (provider_type == "custom" and "/v1" in url) or provider_id in ["mistral", "together", "groq", "cohere"]:
                # OpenAI or compatible (DeepSeek, Groq, Mistral, Together, Cohere etc.)
                headers = {"Authorization": f"Bearer {token}"}
                
                # Special cases for URLs if they aren't fully formed in settings
                if provider_id == "mistral" and not url:
                    url = "https://api.mistral.ai/v1/models"
                elif provider_id == "together" and not url:
                    url = "https://api.together.xyz/v1/models"
                elif provider_id == "cohere" and not url:
                    url = "https://api.cohere.ai/v1/models"
                
                # Resolve base URL from completion URL
                base_url = url.split("/chat/completions")[0] if "/chat/completions" in url else url
                models_url = f"{base_url.rstrip('/')}/models"
                if "/models" in url and provider_id in ["mistral", "together"]: # already has models
                    models_url = url

                resp = requests.get(models_url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    # Handle different response structures
                    if isinstance(data, list):
                        models = [m.get("id", m) for m in data]
                    else:
                        models = [m["id"] for m in data.get("data", [])]
                    
                    # Filter for chat models if possible (heuristic)
                    chat_models = [m for m in models if any(x in m.lower() for x in ["gpt", "claude", "gemini", "llama", "mistral", "mixtral", "deepseek", "qwen", "phi", "gemma"])]
                    return chat_models if chat_models else models
            
            elif provider_type == "ollama":
                # Ollama local API
                base_url = url.rstrip("/")
                resp = requests.get(f"{base_url}/api/tags", timeout=5)
                if resp.status_code == 200:
                    data = resp.json()
                    return [m["name"] for m in data.get("models", [])]
            
            elif provider_type == "huggingface":
                # Hugging Face models list
                try:
                    # Try using params for filtering as suggested by user
                    params = {"pipeline_tag": "text-generation", "limit": 50, "sort": "downloads", "direction": -1}
                    resp = requests.get("https://huggingface.co/api/models", params=params, timeout=10)
                    if resp.status_code == 200:
                        return [m["modelId"] for m in resp.json()]
                except Exception:
                    # Fallback to library if available
                    try:
                        from huggingface_hub import list_models
                        models = list_models(filter="conversational", sort="downloads", direction=-1, limit=30)
                        return [m.id for m in models]
                    except: pass

            elif provider_type == "anthropic":
                # Anthropic doesn't have a public models list endpoint
                return ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"]

            elif provider_type == "google":
                # Google Gemini models
                if token:
                    # Try both Vertex and AI Studio
                    resp = requests.get(f"https://generativelanguage.googleapis.com/v1/models?key={token}", timeout=10)
                    if resp.status_code == 200:
                        data = resp.json()
                        return [m["name"].split("/")[-1] for m in data.get("models", []) if "generateContent" in m.get("supportedGenerationMethods", [])]
                # Static fallback for Gemini
                return ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.0-pro"]

        except Exception as e:
            print(f"Error fetching models for {provider_id}: {e}")
        
        return []

    def get_ollama_library(self):
        """Return a curated list of popular Ollama models for browsing"""
        return [
            "llama3", "llama3:70b", "llama3:8b",
            "deepseek-coder-v2", "deepseek-coder-v2:16b",
            "mistral", "mixtral", "codellama", "phi3",
            "qwen2.5-coder", "qwen2.5", "gemma2",
            "nemotron-3-nano", "olmo-3", "devstral-small-2", "devstral-2",
            "llava", "moondream", "dolphin-mistral",
            "starcoder2", "stable-code"
        ]

    def pull_ollama_model(self, model_name, progress_callback=None):
        """Pull an Ollama model locally"""
        url, _, _, _ = self.get_provider_config("ollama")
        base_url = url.rstrip("/")
        
        try:
            import json
            # Stream the pull response
            resp = requests.post(f"{base_url}/api/pull", json={"name": model_name}, stream=True, timeout=None)
            for line in resp.iter_lines():
                if line:
                    status = json.loads(line)
                    if progress_callback:
                        progress_callback(status)
                    if status.get("status") == "success":
                        return True
            return False
        except Exception as e:
            print(f"Error pulling Ollama model {model_name}: {e}")
            return False

    def delete_ollama_model(self, model_name):
        """Physically delete an Ollama model from local storage"""
        url, _, _, _ = self.get_provider_config("ollama")
        base_url = url.rstrip("/")
        try:
            resp = requests.delete(f"{base_url}/api/delete", json={"name": model_name}, timeout=10)
            return resp.status_code == 200
        except Exception as e:
            print(f"Error deleting Ollama model {model_name}: {e}")
            return False

    def is_ollama_model_downloaded(self, model_name):
        """Check if an Ollama model is already downloaded"""
        downloaded = self.fetch_available_models("ollama")
        # Check for exact match or match without tag
        if model_name in downloaded: return True
        if ":" not in model_name:
            return any(m.startswith(f"{model_name}:") for m in downloaded)
        return False

    def validate_model(self, model_name, provider_id=None):
        """Check if model is allowed for a specific provider or globally"""
        allowed = self.get_allowed_models(provider_id)
        return model_name in allowed

    def reset_to_defaults(self):
        """Reset provider settings to defaults"""
        self.app.settings["custom_providers"] = {}
        self.app.settings["active_providers"] = ["openai"]
        self.app.settings["api_provider"] = "openai"
        self.app.settings["allow_multiple_providers"] = False
        
        # Clear keys (optional, but safer to keep them or clear them?)
        # For a full reset, we'll clear them.
        for pid in self.default_providers:
            key = f"{pid}_key"
            if key in self.app.settings:
                del self.app.settings[key]
        
        self.app.save_settings(self.app.settings)

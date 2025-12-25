"""
Base Agent - Abstract base class for all AI agents
"""
from abc import ABC, abstractmethod
import threading
import queue
import json
from datetime import datetime

class BaseAgent(ABC):
    """Abstract base class for AI agents"""
    
    def __init__(self, name, role, model_provider, model_name, orchestrator=None):
        self.name = name
        self.role = role
        self.model_provider = model_provider  # openai, huggingface, ollama, custom
        self.model_name = model_name
        self.orchestrator = orchestrator
        
        self.status = "idle"  # idle, working, waiting
        self.message_queue = queue.Queue()
        self.history = []  # Conversation history
        self._running = False
        self._thread = None
        self._manual_token = None
        
    def start(self):
        """Start the agent's message processing loop"""
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        
    def stop(self):
        """Stop the agent"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1)
            
    def _run_loop(self):
        """Main processing loop"""
        while self._running:
            try:
                message = self.message_queue.get(timeout=0.5)
                self.status = "working"
                self.receive_message(message["from"], message["content"])
                self.status = "idle"
                try:
                    if hasattr(self.orchestrator, 'app') and self.orchestrator.app:
                        self.orchestrator.app.event_generate('<<AgentDone>>', when='tail')
                except Exception:
                    pass
            except queue.Empty:
                pass
                
    def send_message(self, to_agent, content):
        """Send message to another agent via orchestrator"""
        if self.orchestrator:
            self.orchestrator.route_message(self.name, to_agent, content)
        self.log(f"Sent to {to_agent}: {content[:50]}...")
        
    def receive_message(self, from_agent, content):
        """Handle incoming message"""
        self.log(f"Received from {from_agent}: {content[:50]}...")
        self.history.append({
            "from": from_agent,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        # Process the message
        response = self.process(content)
        return response
        
    def queue_message(self, from_agent, content):
        """Queue a message for processing"""
        self.message_queue.put({"from": from_agent, "content": content})
        
    @abstractmethod
    def process(self, task):
        """Process a task - must be implemented by subclasses"""
        pass
        
    def call_model(self, prompt, system_prompt=None):
        """Call the configured AI model with shared context"""
        # Inject shared history into prompt if available
        context_str = ""
        if self.orchestrator and hasattr(self.orchestrator, 'shared_history'):
            history = self.orchestrator.shared_history[-10:] # Last 10 messages
            if history:
                context_str = "\n--- Recent Inter-Agent Conversation ---\n"
                for msg in history:
                    context_str += f"{msg['from']} to {msg['to']}: {msg['content'][:200]}\n"
                context_str += "--------------------------------------\n\n"
        
        full_prompt = context_str + prompt if context_str else prompt
        
        # Use centralized LLM caller
        try:
            from core.llm import call_llm
            
            # Resolve URL and Key
            provider_type = self.model_provider
            url = ""
            key = ""
            
            if provider_type == "openai":
                url = self._get_setting("openai_url", "https://api.openai.com/v1/chat/completions")
                key = self._get_setting("openai_key", "")
            elif provider_type == "anthropic":
                url = self._get_setting("anthropic_url", "https://api.anthropic.com/v1/messages")
                key = self._get_setting("anthropic_key", "")
            elif provider_type == "google":
                url = self._get_setting("google_url", "https://generativelanguage.googleapis.com/v1/models")
                key = self._get_setting("google_key", "")
            elif provider_type == "ollama":
                url = self._get_setting("ollama_url", "http://localhost:11434")
            elif provider_type == "huggingface":
                url = self._get_setting("huggingface_url", "https://router.huggingface.co/hf-inference/v1/chat/completions")
                key = self._get_hf_token()
            else:
                url = self._get_setting("custom_endpoint", "")
                key = self._get_setting("custom_key", "")

            # Get stop_event if available from orchestrator/app
            stop_event = None
            if self.orchestrator and hasattr(self.orchestrator, 'app') and self.orchestrator.app:
                stop_event = getattr(self.orchestrator.app, 'stop_event', None)

            return call_llm(
                prompt=full_prompt,
                api_url=url,
                model=self.model_name,
                provider=provider_type,
                token=key,
                system_prompt=system_prompt or "You are a helpful AI assistant.",
                stop_event=stop_event,
                role=self.role
            )
        except Exception as e:
            self.log(f"Model call error: {e}")
            return f"Error: {e}"

    def _call_huggingface(self, prompt, system_prompt=None):
        # Deprecated: call_model now uses core.llm directly
        return self.call_model(prompt, system_prompt)
            
    def _call_openai(self, prompt, system_prompt=None):
        # Deprecated: call_model now uses core.llm directly
        return self.call_model(prompt, system_prompt)
        
    def _call_ollama(self, prompt, system_prompt=None):
        # Deprecated: call_model now uses core.llm directly
        return self.call_model(prompt, system_prompt)
        
    def _call_custom(self, prompt, system_prompt=None):
        # Deprecated: call_model now uses core.llm directly
        return self.call_model(prompt, system_prompt)

    def _call_anthropic(self, prompt, system_prompt=None):
        # Deprecated: call_model now uses core.llm directly
        return self.call_model(prompt, system_prompt)

    def _call_gemini(self, prompt, system_prompt=None):
        # Deprecated: call_model now uses core.llm directly
        return self.call_model(prompt, system_prompt)
        
    def _get_hf_token(self):
        return self._manual_token or self._get_setting("hf_key", "")
        
    def set_api_token(self, token):
        """Manually set API token if orchestrator isn't available"""
        self._manual_token = token
        
    def _get_setting(self, key, default=""):
        if self._manual_token and key in ("hf_key", "openai_key", "custom_key"):
            return self._manual_token
        if self.orchestrator and hasattr(self.orchestrator, 'app'):
            return self.orchestrator.app.settings.get(key, default)
        return default
        
    def log(self, message):
        """Log agent activity"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] [{self.name}] {message}"
        print(log_entry)
        if self.orchestrator:
            self.orchestrator.log(log_entry)
            # Pipe to chat if app is available
            if hasattr(self.orchestrator, 'app') and self.orchestrator.app:
                self.orchestrator.app.log_ai_to_chat(self.name, message)
            
    def to_dict(self):
        """Serialize agent state"""
        return {
            "name": self.name,
            "role": self.role,
            "model_provider": self.model_provider,
            "model_name": self.model_name,
            "status": self.status
        }

    def requires_approval(self):
        """Check if actions require user approval"""
        if self.orchestrator:
            # Check orchestrator flag first
            if hasattr(self.orchestrator, 'approval_required') and self.orchestrator.approval_required:
                return True
            # Fallback to app settings
            if hasattr(self.orchestrator, 'app'):
                return not self.orchestrator.app.settings.get("agent_auto_approve", False)
        return True # Default to requiring approval for safety

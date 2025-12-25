"""
GUI Coder Agent - Generates UI code from image analysis
Supports: Tkinter, HTML/CSS, Roblox Lua, Unity C#
"""
from core.base_agent import BaseAgent

class GUICoderAgent(BaseAgent):
    """Agent for GUI code generation from image analysis"""
    
    def __init__(self, name="gui_coder", role="GUI Developer", model_provider="huggingface", model_name="Qwen/Qwen2.5-Coder-7B-Instruct", orchestrator=None):
        super().__init__(name, role, model_provider, model_name, orchestrator)
        self.target_framework = "tkinter"  # Default
        
    def set_framework(self, framework):
        """Set target UI framework"""
        self.target_framework = framework
        self.log(f"Target framework set to: {framework}")
        
    def process(self, task):
        """Process GUI coding task"""
        # Detect framework from task or use default
        framework = self._detect_framework(task)
        
        system_prompt = self._get_system_prompt(framework)
        
        # If receiving image analysis, use that context
        if "IMAGE_ANALYSIS:" in task:
            task = task.replace("IMAGE_ANALYSIS:", "Based on this UI analysis, generate code:\n")
            
        response = self.call_model(task, system_prompt)
        
        # Notify orchestrator that code is ready for preview
        if self.orchestrator:
            self.orchestrator.log(f"GUI code generated for {framework}")
            
        return response
        
    def _detect_framework(self, task):
        """Detect target framework from task"""
        task_lower = task.lower()
        
        if "tkinter" in task_lower or "python gui" in task_lower:
            return "tkinter"
        elif "html" in task_lower or "web" in task_lower or "css" in task_lower:
            return "html"
        elif "roblox" in task_lower or "lua" in task_lower:
            return "roblox"
        elif "unity" in task_lower or "c#" in task_lower:
            return "unity"
        else:
            return self.target_framework
            
    def _get_system_prompt(self, framework):
        """Get framework-specific system prompt"""
        prompts = {
            "tkinter": """You are an expert Python/Tkinter developer.
Generate complete, runnable Tkinter code based on the UI description.
Include:
- All imports
- Proper widget hierarchy
- Layout management (pack/grid/place)
- Styling (colors, fonts)
- Event handlers where appropriate
Output only the Python code.""",

            "html": """You are an expert web developer.
Generate complete HTML and CSS based on the UI description.
Include:
- Semantic HTML5
- Modern CSS (flexbox/grid)
- Responsive design
- Hover states and transitions
Output the HTML with embedded <style> tags.""",

            "roblox": """You are an expert Roblox developer.
Generate Roblox Lua code for a ScreenGui based on the UI description.
Include:
- ScreenGui setup
- Frame hierarchy
- UICorner, UIStroke for styling
- TextLabels, TextButtons, ImageLabels
- Proper anchoring and sizing
Output only the Lua code.""",

            "unity": """You are an expert Unity developer.
Generate C# code for a Unity UI based on the UI description.
Include:
- MonoBehaviour script
- UI element creation/setup
- Canvas and panel hierarchy
- Styling and layout
Output only the C# code."""
        }
        
        return prompts.get(framework, prompts["tkinter"])

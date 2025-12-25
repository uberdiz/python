"""
Planner Agent - Project planning and architecture design
"""
from core.base_agent import BaseAgent

class PlannerAgent(BaseAgent):
    """Agent for project planning and architecture"""
    
    def __init__(self, name="planner", role="Project Planner", model_provider="huggingface", model_name="Qwen/Qwen2.5-7B-Instruct", orchestrator=None):
        super().__init__(name, role, model_provider, model_name, orchestrator)
        
    def process(self, task):
        """Process planning task"""
        # Enhance prompt if it's an image analysis completion
        is_image_completion = "IMAGE_ANALYSIS_COMPLETE" in task
        
        system_prompt = """You are an expert software architect and project planner.
Your job is to create detailed, actionable project plans based on requirements or image analysis results.
Include: Architecture overview, file structure, key components, and implementation steps.
Be specific and practical. Output in markdown format."""

        if is_image_completion:
            system_prompt += "\nThis task is based on an image analysis. Focus on the visual requirements and UI layout described."

        response = self.call_model(task, system_prompt)
        
        # Send plan to coder if available
        if self.orchestrator:
            coder_name = self.orchestrator.find_agent_by_role("coder")
            if coder_name:
                self.send_message(coder_name, f"PLAN_FOR_EXECUTION:\n{response}")
            
        return response

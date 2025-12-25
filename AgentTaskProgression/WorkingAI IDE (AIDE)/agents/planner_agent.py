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
        system_prompt = """You are an expert software architect and project planner.
Your job is to create detailed, actionable project plans.
Include: Architecture overview, file structure, key components, and implementation steps.
Be specific and practical. Output in markdown format."""

        response = self.call_model(task, system_prompt)
        
        # Send plan to coder if available
        if self.orchestrator and "coder" in self.orchestrator.agents:
            self.send_message("coder", f"PLAN:\n{response}")
            
        return response

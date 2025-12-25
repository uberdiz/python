"""
Reviser Agent - Refines and finishes prompts or code suggestions.
"""
from core.base_agent import BaseAgent

class ReviserAgent(BaseAgent):
    """Agent for refining and improving AI-generated content"""
    
    def __init__(self, name="reviser", role="Reviser", model_provider="openai", model_name="gpt-4o-mini", orchestrator=None):
        super().__init__(name, role, model_provider, model_name, orchestrator)
        
    def process(self, task_input):
        """Refine the provided content"""
        # Handle both dict and string input
        if isinstance(task_input, dict):
            content = task_input.get("message", "")
            context = task_input.get("context", "")
        else:
            content = task_input
            context = "Inter-agent workflow"
        
        prompt = f"""You are a professional Prompt and Code Reviser. 
Your task is to take the following raw analysis or prompt and "finish" it - make it professional, concise, and actionable for a developer.

CONTEXT:
{context}

RAW CONTENT:
{content}

REVISION TASK:
1. Remove redundancy.
2. Ensure technical accuracy.
3. Structure it as a clear set of instructions or a final prompt for the next stage.
4. Keep it concise to save tokens.

Final Revised Output:"""

        revised_content = self.call_model(prompt)
        
        # If there's an orchestrator, we might want to send this to the planner or back to the user
        if self.orchestrator:
            # Check if we should trigger the planner
            planner_name = self.orchestrator.find_agent_by_role("Planner")
            if planner_name:
                self.send_message(planner_name, f"REVISED_TASK:\n{revised_content}")
            
            # Also notify the UI about the revised prompt
            if hasattr(self.orchestrator, 'app') and self.orchestrator.app and hasattr(self.orchestrator.app, 'root'):
                self.orchestrator.app.root.after(0, lambda: self.orchestrator.app.ai_panel.add_chat_message(f"🤖 {self.name}", f"Revised Prompt:\n{revised_content}"))
            
        return revised_content

"""
Tester Agent - Runs tests and reports failures
"""
from core.base_agent import BaseAgent
import subprocess
import os

class TesterAgent(BaseAgent):
    """Agent for test execution and failure reporting"""
    
    def __init__(self, name="tester", role="Test Runner", model_provider="huggingface", model_name="Qwen/Qwen2.5-7B-Instruct", orchestrator=None):
        super().__init__(name, role, model_provider, model_name, orchestrator)
        
    def process(self, task):
        """Process testing task"""
        # If receiving code, analyze and test it
        if "CODE:" in task:
            code_content = task.replace("CODE:", "").strip()
            return self.analyze_code(code_content)
            
        # If task is a file path, run tests on it
        if os.path.exists(task.strip()):
            return self.run_tests(task.strip())
            
        # Otherwise, use AI to suggest tests
        return self.suggest_tests(task)
        
    def run_tests(self, file_path):
        """Run pytest on the file"""
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", file_path, "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=os.path.dirname(file_path) or "."
            )
            
            output = result.stdout + result.stderr
            
            # Check for failures
            if "FAILED" in output or result.returncode != 0:
                self.log("Tests failed, notifying coder...")
                if self.orchestrator and "coder" in self.orchestrator.agents:
                    self.send_message("coder", f"TEST_FAILURES:\n{output}")
            else:
                self.log("All tests passed!")
                
            return output
            
        except subprocess.TimeoutExpired:
            return "Test timeout (60s)"
        except Exception as e:
            return f"Test error: {e}"
            
    def analyze_code(self, code):
        """Analyze code for potential issues"""
        system_prompt = """You are a code reviewer and tester.
Analyze this code for:
1. Syntax errors
2. Logic bugs
3. Missing error handling
4. Security issues
5. Performance problems
Provide specific line numbers and fixes."""

        return self.call_model(f"Review this code:\n```\n{code}\n```", system_prompt)
        
    def suggest_tests(self, description):
        """Suggest test cases based on description"""
        system_prompt = """You are a test engineer.
Generate pytest test cases for the described functionality.
Include:
- Unit tests
- Edge cases
- Error conditions
Output only the Python test code."""

        return self.call_model(f"Generate tests for:\n{description}", system_prompt)

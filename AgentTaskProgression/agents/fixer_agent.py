"""
Fixer Agent - Specialized in fixing errors and passing tests
"""
from core.base_agent import BaseAgent
import os
import json
import subprocess
import threading
from core.llm import call_llm

class FixerAgent(BaseAgent):
    """Agent specialized in fixing code errors and ensuring tests pass"""
    
    def __init__(self, name="fixer", role="Fixer", model_provider="openai", model_name="gpt-4o", orchestrator=None):
        super().__init__(name, role, model_provider, model_name, orchestrator)
        self.max_iterations = 3
        
    def process(self, task):
        """Process fixing task"""
        if "TEST_FAILURES:" in task:
            error_log = task.replace("TEST_FAILURES:", "").strip()
            return self.fix_errors(error_log)
        
        if "ERROR:" in task:
            error_log = task.replace("ERROR:", "").strip()
            return self.fix_errors(error_log)
            
        return "I can help fix errors. Please provide the error log or test failures."

    def fix_errors(self, error_log):
        """Attempt to fix errors iteratively"""
        self.log(f"Starting fix process for errors: {error_log[:100]}...")
        
        project_path = getattr(self.orchestrator.app, 'project_path', None) if self.orchestrator else None
        if not project_path:
            return "Error: No project path found."

        # Get relevant files from error log
        files_to_fix = self._extract_files_from_error(error_log)
        if not files_to_fix:
            # If no files found, try to fix current open file
            if hasattr(self.orchestrator.app, 'editor_tabs'):
                current_file = self.orchestrator.app.editor_tabs.get_current_file()
                if current_file:
                    files_to_fix = [current_file]

        if not files_to_fix:
            return "Could not identify which files to fix from the error log."

        for iteration in range(self.max_iterations):
            self.log(f"Fix iteration {iteration + 1}/{self.max_iterations}")
            
            # Read file contents
            file_contents = {}
            for f in files_to_fix:
                try:
                    with open(f, 'r', encoding='utf-8') as file:
                        file_contents[f] = file.read()
                except Exception as e:
                    self.log(f"Error reading {f}: {e}")

            # Generate fix prompt
            prompt = self._build_fix_prompt(error_log, file_contents)
            
            # Call LLM
            response = self.call_model(prompt, "You are an expert debugger. Provide fixes in JSON format.")
            
            # Parse fixes
            fixes = self._parse_json_response(response)
            if not fixes:
                self.log("Failed to parse fixes from AI response.")
                continue

            # Apply fixes
            for f, content in fixes.items():
                try:
                    # Resolve path
                    full_path = f if os.path.isabs(f) else os.path.join(project_path, f)
                    with open(full_path, 'w', encoding='utf-8') as file:
                        file.write(content)
                    self.log(f"Applied fix to {f}")
                except Exception as e:
                    self.log(f"Error applying fix to {f}: {e}")

            # Run tests to verify
            test_result = self._run_tests(project_path)
            if test_result["passed"]:
                self.log("Fix successful! All tests passed.")
                return f"Successfully fixed errors after {iteration + 1} iterations."
            else:
                self.log(f"Tests still failing: {test_result['output'][:100]}...")
                error_log = test_result["output"] # Update error log for next iteration

        return f"Failed to fix errors after {self.max_iterations} iterations."

    def _extract_files_from_error(self, error_log):
        """Extract Python filenames from error log"""
        import re
        # Look for patterns like "File 'path/to/file.py', line 123"
        pattern = r'File "(.*\.py)", line \d+'
        files = re.findall(pattern, error_log)
        # Deduplicate and return absolute paths if possible
        unique_files = list(set(files))
        return unique_files

    def _build_fix_prompt(self, error_log, file_contents):
        prompt = f"Fix the following errors:\n\nERRORS:\n{error_log}\n\n"
        prompt += "CURRENT FILE CONTENTS:\n"
        for f, content in file_contents.items():
            prompt += f"--- {f} ---\n{content}\n"
        
        prompt += "\nReturn a JSON object where keys are filenames and values are the COMPLETE corrected file contents.\n"
        prompt += 'Example: {"file1.py": "code...", "file2.py": "code..."}'
        return prompt

    def _parse_json_response(self, response):
        try:
            # Find JSON block
            import re
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            return json.loads(response)
        except Exception:
            return None

    def _run_tests(self, project_path):
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=project_path
            )
            return {
                "passed": result.returncode == 0,
                "output": result.stdout + result.stderr
            }
        except Exception as e:
            return {"passed": False, "output": str(e)}

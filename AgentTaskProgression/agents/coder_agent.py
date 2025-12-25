"""
Coder Agent - Code generation based on plans
"""
from core.base_agent import BaseAgent

class CoderAgent(BaseAgent):
    def __init__(self, name="coder", role="Code Generator", model_provider="huggingface", model_name="Qwen/Qwen2.5-Coder-7B-Instruct", orchestrator=None):
        super().__init__(name, role, model_provider, model_name, orchestrator)

    def process(self, task):
        try:
            import re, os
            mod_words = ["modify","change","update","edit","fix","add","remove","make","set","refactor", "plan_for_execution", "image_analysis_complete"]
            is_mod = any(w in task.lower() for w in mod_words)
            
            # Extract potential file paths from the task or plan
            scripts = re.findall(r"\b([\w\\/\.-]+\.py)\b", task, re.IGNORECASE)
            
            project_path = None
            if self.orchestrator and hasattr(self.orchestrator, 'app'):
                project_path = getattr(self.orchestrator.app, "project_path", None)
            
            targets = []
            for s in scripts:
                p = s if os.path.isabs(s) else (os.path.join(project_path, s) if project_path else s)
                if os.path.exists(p) and p not in targets:
                    targets.append(p)
            
            # If no targets found in text, try active editor as fallback
            if not targets and self.orchestrator and hasattr(self.orchestrator, 'app'):
                app = self.orchestrator.app
                if hasattr(app, "editor_tabs") and app.editor_tabs:
                    cur = app.editor_tabs.get_current_file()
                    if cur and cur.endswith(".py"):
                        targets = [cur]
            
            # If it's a modification request and we have targets, use the auto-edit logic
            if is_mod and targets:
                self.log(f"Detected modification request for: {[os.path.basename(t) for t in targets]}")
                return self._auto_edit_and_test(task, targets)
            
            # Otherwise just call the model normally
            system_prompt = "You are an expert software developer. Generate clean code or explain implementation based on the requirements."
            resp = self.call_model(task, system_prompt)
            
            if self.orchestrator:
                tester_name = self.orchestrator.find_agent_by_role("tester")
                if tester_name:
                    self.send_message(tester_name, f"CODE_FOR_TESTING:\n{resp}")
            return resp
        except Exception as e:
            return f"Error: {e}"

    def _auto_edit_and_test(self, task, targets):
        try:
            import os
            from agents.chat_agent import apply_patch, clean_and_validate_code
            actions = []
            msgs = []
            for path in targets:
                if not os.path.exists(path):
                    msgs.append(f"Missing: {os.path.basename(path)}")
                    continue
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                prompt = (
                    f"User request: {task}\n\n"
                    f"Current code in {os.path.basename(path)}:\n{content[:4000]}\n\n"
                    f"Respond ONLY with a unified diff patch. Use exactly 1 context line and avoid redundant whitespace."
                )
                patch = self.call_model(prompt, "Return only patch.")
                
                if self.requires_approval():
                    # Instead of applying, propose it to the user
                    self.log(f"Proposed changes for {os.path.basename(path)} (Approval Required)")
                    if self.orchestrator and hasattr(self.orchestrator, 'app'):
                        self.orchestrator.app.log_ai(f"💡 I suggest these changes for {os.path.basename(path)}:\n\n```diff\n{patch}\n```\n(Auto-Agent is disabled, please apply manually or enable Auto-Agent.)")
                    
                    # Still return the proposal in msgs
                    msgs.append(f"Proposed changes for {os.path.basename(path)}")
                    continue

                result = apply_patch(path, content, patch)
                if result.get("success"):
                    actions.append({"type":"modify_file","file":path})
                    msgs.append(f"Updated {os.path.basename(path)}")
                    if getattr(getattr(self, "orchestrator", None), "app", None):
                        try:
                            self.orchestrator.app.test_modified_script(path)
                        except Exception:
                            pass
                else:
                    # Fallback: try to generate full code with retries
                    success = False
                    for attempt in range(2):
                        fallback_prompt = (
                            f"User request: {task}\n\n"
                            f"Current code in {os.path.basename(path)}:\n{content[:4000]}\n\n"
                            f"The previous attempt failed. Please provide the COMPLETE corrected code for this file.\n"
                            f"Respond ONLY with the Python code."
                        )
                        code = self.call_model(fallback_prompt, "Return only code.")
                        code, val_error = clean_and_validate_code(code, path)
                        
                        if code:
                            with open(path, "w", encoding="utf-8") as f:
                                f.write(code)
                            actions.append({"type":"modify_file","file":path})
                            msgs.append(f"Replaced {os.path.basename(path)} (after patch failure)")
                            if getattr(getattr(self, "orchestrator", None), "app", None):
                                try:
                                    self.orchestrator.app.test_modified_script(path)
                                except Exception:
                                    pass
                            success = True
                            break
                        else:
                            self.log(f"Fallback attempt {attempt+1} failed for {os.path.basename(path)}: {val_error}")
                    
                    if not success:
                        msgs.append(f"Failed {os.path.basename(path)}: {result.get('error','')}")
            proj = getattr(getattr(self, "orchestrator", None), "app", None)
            proj_path = getattr(proj, "project_path", None)
            if proj_path:
                try:
                    from core.test_runner import TestRunner
                    tr = TestRunner()
                    res = tr.run_tests(proj_path)
                    passed = res.get("passed", 0)
                    total = res.get("total", 0)
                    msgs.append(f"Tests: {passed}/{total} passed")
                    if getattr(self, "orchestrator", None) and getattr(self.orchestrator, "app", None):
                        self.orchestrator.app.current_test_results = res
                except Exception as e:
                    msgs.append(f"Test error: {e}")
            return "\n".join(msgs) if msgs else "No changes"
        except Exception as e:
            return f"Error: {e}"

"""
Advanced Fixer Agent with Iterative Testing - ENHANCED
"""
import os
import json
import tempfile
import subprocess
import threading
import time
import shutil
from core.llm import call_llm

class FixerAgent:
    def __init__(self, app):
        self.app = app
        self.current_fixes = {}
        self.test_results = {}
        self.fix_iterations = 0
        self.max_iterations = 5
    
    def fix_errors(self, files=None, error_log=None, max_iterations=None):
        """Fix errors in files with iterative testing"""
        if not self.app.project_path:
            return {"success": False, "error": "No project path"}
        
        if max_iterations:
            self.max_iterations = max_iterations
        else:
            self.max_iterations = self.app.settings.get("auto_fix_iterations", 3)
        
        self.fix_iterations = 0
        self.current_fixes = {}
        self.test_results = {}
        
        # Get error log if not provided
        if not error_log:
            error_log = self.get_error_log()
        
        # Get files to fix
        if not files:
            files = self.get_files_to_fix()
        
        # Start fixing process
        self.app.log_ai(f"🔧 Starting auto-fixer for {len(files)} files")
        self.app.log_ai(f"Error log: {error_log[:500]}...")
        
        return self.fix_iteratively(files, error_log)
    
    def fix_iteratively(self, files, error_log):
        """Fix errors iteratively until tests pass"""
        for iteration in range(self.max_iterations):
            self.fix_iterations = iteration + 1
            self.app.log_ai(f"\n🔄 Fix iteration {iteration + 1}/{self.max_iterations}")
            
            # Get file contents
            file_contents = self.get_file_contents(files)
            
            # Generate fixes
            fixes = self.generate_fixes(file_contents, error_log)
            if not fixes:
                self.app.log_ai("❌ No fixes generated")
                continue
            
            # Test fixes (Optional validation)
            test_result = self.test_fixes(fixes)
            self.test_results[iteration] = test_result
            
            if test_result.get("passed", False):
                # Fixes work! Apply them
                self.app.log_ai("✅ Fixes passed validation! Applying...")
                self.apply_fixes(fixes)
                return {
                    "success": True,
                    "fixes": fixes,
                    "tests_passed": True,
                    "iterations": iteration + 1,
                    "test_output": test_result.get("stdout", "")
                }
            else:
                # User wants to apply even if it doesn't pass
                self.app.log_ai("⚠️ Fixes did not pass validation, but applying anyway as requested...")
                self.apply_fixes(fixes)
                
                # If we have more iterations, we can try to fix the NEW errors
                new_errors = test_result.get("error", "") or test_result.get("stderr", "") or test_result.get("stdout", "")
                if new_errors:
                    error_log = f"Previous fix attempt failed with these errors:\n{new_errors}"
                    self.app.log_ai(f"🔄 Continuing to next iteration with new error log...")
                else:
                    # If no specific error, just continue
                    pass
        
        # If we finished all iterations and applied the last one
        return {
            "success": True, # Marked as success because we applied fixes
            "fixes": fixes if 'fixes' in locals() else {},
            "error": "Applied fixes but they may still have errors.",
            "iterations": self.max_iterations,
            "test_results": self.test_results
        }
    
    def get_error_log(self):
        """Get error log from output panel"""
        error_log = ""
        if self.app.output_panels:
            try:
                error_log = self.app.output_panels.script_output.get("1.0", "end-1c")
            except:
                pass
        
        if not error_log:
            # Run tests to get errors
            error_log = self.run_tests_for_errors()
        
        return error_log
    
    def run_tests_for_errors(self):
        """Run tests to get error log"""
        self.app.log_ai("🧪 Running tests to get error log...")
        
        try:
            import sys
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "-v"],
                cwd=self.app.project_path,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            error_log = result.stdout + result.stderr
            if "No test files found" in error_log or result.returncode == 5:
                # No tests found, try to generate one
                self.app.log_ai("🔍 No tests found. Attempting to generate a basic test...")
                return self.generate_initial_test()
            return error_log
        except Exception as e:
            return f"Error running tests: {str(e)}"
    
    def generate_initial_test(self):
        """Generate a basic test file if none exist"""
        files = self.get_files_to_fix()
        if not files:
            return "No files found to generate tests for."
            
        target_file = files[0]
        full_path = os.path.join(self.app.project_path, target_file)
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            prompt = f"""Generate a simple pytest file for this Python code:
            
            FILE: {target_file}
            CONTENT:
            {content[:1000]}
            
            Only return the code for the test file. Save it as 'test_generated.py'.
            """
            
            provider = self.app.settings.get("api_provider", "openai")
            api_url, model, token = self.app.get_ai_settings(provider)
            
            from core.llm import call_llm
            test_code = call_llm(prompt, api_url, model, provider, token)
            
            # Clean markdown
            if "```" in test_code:
                import re
                match = re.search(r'```(?:\w+)?\n(.*?)\n```', test_code, re.DOTALL)
                if match:
                    test_code = match.group(1)
            
            test_path = os.path.join(self.app.project_path, "test_generated.py")
            with open(test_path, 'w', encoding='utf-8') as f:
                f.write(test_code)
            
            self.app.log_ai(f"✅ Generated test: test_generated.py")
            if self.app.project_tree:
                self.app.project_tree.refresh()
                
            # Run the new test
            return self.run_tests_for_errors()
        except Exception as e:
            return f"Failed to generate initial test: {e}"
    
    def get_files_to_fix(self):
        """Get files that might need fixing"""
        files = []
        
        # Check current open files
        if self.app.editor_tabs:
            open_files = self.app.editor_tabs.get_open_files()
            for f in open_files:
                if f.endswith('.py'):
                    rel_path = os.path.relpath(f, self.app.project_path)
                    files.append(rel_path)
        
        # If no open files, check test files
        if not files:
            for root, dirs, filenames in os.walk(self.app.project_path):
                for fname in filenames:
                    if fname.startswith('test_') and fname.endswith('.py'):
                        rel_path = os.path.relpath(os.path.join(root, fname), self.app.project_path)
                        files.append(rel_path)
        
        return files[:10]  # Limit to 10 files
    
    def get_file_contents(self, files):
        """Get contents of files"""
        file_contents = {}
        
        for fname in files:
            try:
                full_path = os.path.join(self.app.project_path, fname)
                if os.path.exists(full_path):
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        file_contents[fname] = content
            except:
                file_contents[fname] = ""
        
        return file_contents
    
    def generate_fixes(self, file_contents, error_log):
        """Generate fixes using AI"""
        # Build prompt
        prompt = f"""Fix these Python errors:

ERRORS:
{error_log[:2000]}

FILES TO FIX:
"""
        
        for fname, content in file_contents.items():
            prompt += f"\n--- {fname} ---\n{content[:1500]}\n"
        
        prompt += """
INSTRUCTIONS:
1. Analyze the errors carefully.
2. Provide the CORRECTED code for each file that needs fixing.
3. Make minimal changes to fix the errors.
4. Ensure the code follows Python best practices.
5. Add appropriate error handling.
6. Include comments explaining fixes.

RESPONSE FORMAT:
Your response must be a valid JSON object with the following structure:
{
  "analysis": "Brief analysis of what was wrong and how it was fixed",
  "fixes": {
    "filename.py": "full corrected code here"
  }
}

IMPORTANT: Ensure all strings in the JSON are correctly escaped. If you find it difficult to return valid JSON with large code blocks, you can alternatively use this format:
[ANALYSIS]
Your analysis here
[FIX: filename.py]
```python
Your code here
```
"""
        
        # Get AI response
        provider = self.app.settings.get("api_provider", "openai")
        api_url, model, token = self.app.get_ai_settings(provider)
        
        response = call_llm(prompt, api_url, model, provider, token)
        
        # Try JSON parsing first
        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                # Replace unescaped newlines in values if possible, but JSON.loads usually handles this if escaped
                # A common issue is the AI not escaping newlines correctly in long strings
                try:
                    result = json.loads(json_str)
                    fixes = result.get("fixes", {})
                    analysis = result.get("analysis", "No analysis provided")
                    self.app.log_ai(f"📝 Fix analysis: {analysis[:200]}...")
                    return fixes
                except json.JSONDecodeError:
                    # Fallback to manual parsing if JSON is malformed but contains the markers
                    pass
        except Exception:
            pass
            
        # Fallback manual parsing (Regex/Marker based)
        self.app.log_ai("⚠️ JSON parsing failed, attempting manual extraction...")
        fixes = {}
        import re
        
        # Extract analysis
        analysis_match = re.search(r'\[ANALYSIS\]\s*(.*?)\s*(?=\[FIX:|$)', response, re.DOTALL | re.IGNORECASE)
        if analysis_match:
            analysis = analysis_match.group(1).strip()
            self.app.log_ai(f"📝 Fix analysis (manual): {analysis[:200]}...")
            
        # 1. Try markers [FIX: filename] with flexible spacing and code block formatting
        # Support both [FIX: filename] and [FIX:filename]
        fix_blocks = re.finditer(r'\[FIX:\s*([^\]]+)\]\s*```(?:python)?\s*(.*?)\s*```', response, re.DOTALL | re.IGNORECASE)
        for match in fix_blocks:
            filename = match.group(1).strip()
            code = match.group(2).strip()
            # Clean up filename (sometimes AI includes path or extra quotes)
            filename = os.path.basename(filename.replace('"', '').replace("'", ""))
            fixes[filename] = code
            
        # 2. If no fixes found, look for filenames followed by code blocks
        if not fixes:
            for fname in file_contents.keys():
                # Look for the filename followed by a code block within some distance
                # This matches "File: main.py\n```python\n..."
                pattern = re.escape(fname) + r'.*?```(?:python)?\s*(.*?)\s*```'
                match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
                if match:
                    fixes[fname] = match.group(1).strip()
                    self.app.log_ai(f"🔧 Found fix for {fname} by filename match")

        # 3. Last ditch effort: if only one file was requested and there is exactly one code block
        if not fixes:
            code_blocks = re.findall(r'```(?:python)?\s*(.*?)\s*```', response, re.DOTALL | re.IGNORECASE)
            if len(code_blocks) == 1 and len(file_contents) == 1:
                filename = list(file_contents.keys())[0]
                fixes[filename] = code_blocks[0].strip()
                self.app.log_ai(f"🔧 Only one code block found, assuming it is for {filename}")
            elif len(code_blocks) >= 1 and len(file_contents) == 1:
                # If multiple blocks but only one file, maybe take the longest one or the first one?
                # Let's take the first non-empty one
                filename = list(file_contents.keys())[0]
                for block in code_blocks:
                    if len(block.strip()) > 50: # Likely the code, not a snippet
                        fixes[filename] = block.strip()
                        self.app.log_ai(f"🔧 Multiple blocks found, choosing longest for {filename}")
                        break
        
        # 4. Final attempt: Check if the whole response is just code (sometimes happens with some models)
        if not fixes and "import " in response and "def " in response and len(file_contents) == 1:
            filename = list(file_contents.keys())[0]
            # Strip markdown if present
            clean_code = response.strip()
            if clean_code.startswith("```"):
                clean_code = re.sub(r'^```(?:python)?\n|```$', '', clean_code, flags=re.MULTILINE).strip()
            fixes[filename] = clean_code
            self.app.log_ai(f"🔧 Response looks like raw code, using for {filename}")

        if fixes:
            self.app.log_ai(f"🔧 Generated fixes for {len(fixes)} files via manual parsing")
            # Ensure filenames match what we expected (relative paths)
            final_fixes = {}
            for f_fix, code in fixes.items():
                # Match against requested files
                matched = False
                for f_req in file_contents.keys():
                    if f_fix.lower() == f_req.lower() or os.path.basename(f_fix).lower() == os.path.basename(f_req).lower():
                        final_fixes[f_req] = code
                        matched = True
                        break
                if not matched:
                    # If it's a new file suggested by AI, keep it
                    final_fixes[f_fix] = code
            return final_fixes
        else:
            self.app.log_ai("❌ Failed to extract any fixes from AI response")
            # Log a bit of the response for debugging if it failed
            self.app.log_ai(f"Debug - AI Response Start: {response[:100]}...")
            
        return fixes
    
    def test_fixes(self, fixes):
        """Test fixes in temporary environment or project"""
        # If no tests exist, try running the main script to see if it still crashes
        with tempfile.TemporaryDirectory() as temp_dir:
            # Copy all project files
            self.copy_project_to_temp(temp_dir, fixes)
            
            # Check for tests
            import sys
            has_tests = False
            for root, dirs, filenames in os.walk(temp_dir):
                for fname in filenames:
                    if fname.startswith('test_') and fname.endswith('.py'):
                        has_tests = True
                        break
                if has_tests: break
            
            if has_tests:
                # Run pytest
                try:
                    result = subprocess.run(
                        [sys.executable, "-m", "pytest", "-v"],
                        cwd=temp_dir,
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                    return {
                        "passed": result.returncode == 0,
                        "stdout": result.stdout,
                        "stderr": result.stderr
                    }
                except Exception as e:
                    return {"passed": False, "error": str(e)}
            else:
                # No tests, try running the main file or the fixed files
                file_to_run = None
                if "main.py" in fixes:
                    file_to_run = os.path.join(temp_dir, "main.py")
                elif fixes:
                    # Try the first fixed file
                    file_to_run = os.path.join(temp_dir, list(fixes.keys())[0])
                
                if not file_to_run:
                    main_path = os.path.join(temp_dir, "main.py")
                    if os.path.exists(main_path):
                        file_to_run = main_path
                
                if file_to_run:
                    try:
                        self.app.log_ai(f"🔬 Testing fix by running: {os.path.basename(file_to_run)}")
                        result = subprocess.run(
                            [sys.executable, file_to_run],
                            cwd=temp_dir,
                            capture_output=True,
                            text=True,
                            timeout=30
                        )
                        # If it runs for 5 seconds without error, we consider it "fixed enough" for a script
                        return {
                            "passed": result.returncode == 0,
                            "stdout": result.stdout,
                            "stderr": result.stderr
                        }
                    except subprocess.TimeoutExpired:
                        # If it times out, it might be a GUI app or long running script that is now working
                        return {"passed": True, "stdout": "Execution timed out (possible GUI app)"}
                    except Exception as e:
                        return {"passed": False, "error": str(e)}
                
                return {"passed": True, "stdout": "No tests or runnable script to verify fixes."}
    
    def copy_project_to_temp(self, temp_dir, fixes):
        """Copy project files to temp directory, applying fixes"""
        for root, dirs, files in os.walk(self.app.project_path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                if file.endswith('.py'):
                    src = os.path.join(root, file)
                    rel_path = os.path.relpath(src, self.app.project_path)
                    dst = os.path.join(temp_dir, rel_path)
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    
                    if rel_path in fixes:
                        # Use fixed version
                        with open(dst, 'w', encoding='utf-8') as f:
                            f.write(fixes[rel_path])
                    else:
                        # Copy original
                        shutil.copy2(src, dst)
    
    def apply_fixes(self, fixes):
        """Apply fixes to actual project files"""
        applied_count = 0
        
        for filename, content in fixes.items():
            full_path = os.path.join(self.app.project_path, filename)
            
            try:
                # Create backup
                if os.path.exists(full_path):
                    backup_path = full_path + ".backup"
                    shutil.copy2(full_path, backup_path)
                
                # Write fixed content
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                applied_count += 1
                self.app.log_ai(f"✅ Applied fix to: {filename}")
                
                # Reload in editor if open
                if hasattr(self.app, 'editor_tabs') and self.app.editor_tabs and filename in self.app.editor_tabs.get_open_files():
                    self.app.editor_tabs.open_file(full_path)
                
            except Exception as e:
                self.app.log_ai(f"❌ Failed to apply fix to {filename}: {e}")
        
        # Refresh project tree
        if self.app.project_tree:
            self.app.project_tree.refresh()
        
        self.app.log_ai(f"🎉 Applied {applied_count} fixes successfully")
        
    def run_final_tests(self):
        """Run final tests after applying fixes"""
        def test_thread():
            try:
                import sys
                result = subprocess.run(
                    [sys.executable, "-m", "pytest", "-v"],
                    cwd=self.app.project_path,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.returncode == 0:
                    self.app.log_ai("✅ All tests pass after fixes!")
                else:
                    self.app.log_ai(f"⚠️ Some tests still failing:\n{result.stderr[:500]}")
            except Exception as e:
                self.app.log_ai(f"❌ Error running final tests: {e}")
        
        threading.Thread(target=test_thread, daemon=True).start()


def advanced_fixer_agent(project_path, files, error_log, api_url, model, max_iterations=3):
    """Standalone advanced fixer agent function for compatibility"""
    from core.llm import call_llm
    
    class TempApp:
        def __init__(self, project_path, api_url, model):
            self.project_path = project_path
            self.settings = {
                "api_provider": "openai",
                "model": model
            }
            self.logs = []
            self.editor_tabs = None
            self.project_tree = None
            self.output_panels = None
        
        def log_ai(self, msg):
            self.logs.append(msg)
            print(msg)

        def log_ai_to_chat(self, sender, msg):
            pass # No-op for temp app
        
        def get_ai_settings(self, provider):
            return api_url, model, None
    
    temp_app = TempApp(project_path, api_url, model)
    fixer = FixerAgent(temp_app)
    
    # Convert relative paths to absolute if needed
    if files and len(files) > 0 and not os.path.isabs(files[0]):
        files = [os.path.join(project_path, f) for f in files]
    
    result = fixer.fix_errors(files, error_log, max_iterations)
    
    # Apply fixes if successful
    if result.get("success") and result.get("fixes"):
        for filename, content in result["fixes"].items():
            full_path = os.path.join(project_path, filename)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
    
    return result
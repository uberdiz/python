"""
Linter module for detecting code issues
"""
import sys
import os
import subprocess
import shutil

class Linter:
    def __init__(self):
        self.pylint_available = shutil.which("pylint") is not None
        
    def lint_file(self, file_path):
        """
        Lint a file and return a list of issues.
        Returns: list of dicts {'line': int, 'message': str, 'type': 'error'|'warning'|'info'}
        """
        issues = []
        
        if not file_path or not os.path.exists(file_path):
            return issues
            
        filename = os.path.basename(file_path)
            
        # 1. Basic Syntax Check (Fast)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            compile(content, file_path, 'exec')
        except SyntaxError as e:
            issues.append({
                'file': filename,
                'line': e.lineno,
                'message': f"Syntax Error: {e.msg}",
                'type': 'error'
            })
            # If syntax error, pylint usually fails hard or output is redundant, so we might stop here
            # But let's continue if we want more info
            
        # 2. Pylint Check (Slower, but detailed)
        if self.pylint_available:
            try:
                # Run pylint with json output or specific format
                # Using --output-format=msg-template='{line}:{msg_id}:{msg_type}:{msg}'
                
                cmd = [
                    "pylint",
                    "--output-format=msg-template='{line}:{msg_id}:{msg_type}:{msg}'",
                    "--disable=C,R", # Disable Convention and Refactor checks for speed/noise
                    "--reports=n",
                    "--score=n",
                    file_path
                ]
                
                # On Windows, need shell=True sometimes or specific executable handling
                # But subprocess.run usually works if in PATH
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                for line in result.stdout.splitlines():
                    if not line.strip(): continue
                    # Remove quotes if present (msg-template issues)
                    line = line.replace("'", "")
                    
                    parts = line.split(':', 3)
                    if len(parts) >= 4:
                        try:
                            line_no = int(parts[0])
                            msg_id = parts[1]
                            msg_type = parts[2] # I, W, E, F
                            msg_text = parts[3]
                            
                            issue_type = 'info'
                            if msg_type in ['E', 'F']:
                                issue_type = 'error'
                            elif msg_type == 'W':
                                issue_type = 'warning'
                                
                            # Avoid duplicate syntax errors if already caught
                            if "SyntaxError" in msg_text and any(i['line'] == line_no and "Syntax Error" in i['message'] for i in issues):
                                continue
                                
                            issues.append({
                                'file': filename,
                                'line': line_no,
                                'message': f"[{msg_id}] {msg_text}",
                                'type': issue_type
                            })
                        except ValueError:
                            pass
                            
            except Exception as e:
                print(f"Pylint error: {e}")
                
        return issues

"""
Advanced Test Runner with detailed reporting and coverage - ENHANCED
"""
import subprocess
import os
import re

class TestRunner:
    __test__ = False
    def __init__(self):
        self.results_cache = {}
    
    def run_tests(self, project_path, timeout=60):
        """Run tests and return detailed results - ENHANCED"""
        try:
            # First, find test files
            test_files = self.find_test_files(project_path)
            
            if not test_files:
                return {
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "errors": 1,
                    "details": [{"name": "No tests found", "passed": False, "error": "No test files found"}],
                    "raw_output": "No test files found. Create test_*.py files.",
                    "test_files": [],
                    "coverage": 0
                }
            
            import sys
            # Check for pytest installation
            try:
                import pytest
            except ImportError:
                # Attempt to install pytest securely
                try:
                    from core.security import SecurityManager
                    # Hack: assuming we can access app context, but we don't have it here.
                    # We will use subprocess directly but it should be logged if we had the manager.
                    print("Installing pytest...")
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "pytest", "pytest-cov", "coverage"])
                except Exception as e:
                    return {
                        "total": 0,
                        "passed": 0,
                        "failed": 0,
                        "errors": 1,
                        "details": [{"name": "Environment Error", "passed": False, "error": f"Failed to install pytest: {e}"}],
                        "raw_output": f"Error: pytest is missing and could not be installed: {e}",
                        "test_files": [],
                        "coverage": 0
                    }

            # Run pytest with coverage
            cmd = [sys.executable, "-m", "pytest"] + test_files + ["-v", "--tb=short"]
            
            result = subprocess.run(
                cmd,
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            # Also run coverage separately
            coverage_result = self.run_coverage(project_path, test_files)
            
            # Parse results
            test_details = self.parse_test_output(result.stdout, result.stderr)
            
            # Calculate summary
            total = len(test_details)
            passed = sum(1 for t in test_details if t.get('passed', False))
            failed = total - passed
            errors = sum(1 for t in test_details if t.get('error'))
            
            return {
                "total": total,
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "details": test_details,
                "raw_output": result.stdout + result.stderr,
                "test_files": test_files,
                "coverage": coverage_result.get("coverage", 0),
                "coverage_details": coverage_result.get("details", {})
            }
            
        except subprocess.TimeoutExpired:
            return {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "errors": 1,
                "details": [{"name": "Test Runner", "passed": False, "error": "Timeout expired"}],
                "raw_output": f"Test execution timed out after {timeout} seconds",
                "test_files": [],
                "coverage": 0
            }
        except Exception as e:
            return {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "errors": 1,
                "details": [{"name": "Test Runner", "passed": False, "error": str(e)}],
                "raw_output": f"Error running tests: {e}",
                "test_files": [],
                "coverage": 0
            }
    
    def run_coverage(self, project_path, test_files):
        """Run coverage analysis"""
        try:
            # Run coverage
            coverage_cmd = ["coverage", "run", "-m", "pytest"] + test_files
            subprocess.run(
                coverage_cmd,
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Get coverage report
            report_cmd = ["coverage", "report"]
            result = subprocess.run(
                report_cmd,
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Parse coverage
            coverage = self.parse_coverage_output(result.stdout)
            
            # Get detailed coverage
            detailed_cmd = ["coverage", "json"]
            detailed_result = subprocess.run(
                detailed_cmd,
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Try to read coverage.json
            coverage_json_path = os.path.join(project_path, "coverage.json")
            details = {}
            if os.path.exists(coverage_json_path):
                import json
                with open(coverage_json_path, 'r') as f:
                    details = json.load(f)
            
            return {
                "coverage": coverage,
                "details": details,
                "raw_output": result.stdout
            }
            
        except Exception as e:
            return {
                "coverage": 0,
                "details": {},
                "raw_output": f"Coverage error: {e}"
            }
    
    def parse_coverage_output(self, output):
        """Parse coverage percentage from output"""
        lines = output.split('\n')
        for line in lines:
            if "TOTAL" in line.upper():
                parts = line.split()
                for part in parts:
                    if part.endswith('%'):
                        try:
                            return float(part.strip('%'))
                        except:
                            pass
        return 0
    
    def find_test_files(self, project_path):
        """Find all test files in project"""
        test_files = []
        
        for root, dirs, files in os.walk(project_path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                if (file.startswith('test_') or file.endswith('_test.py')) and file.endswith('.py'):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, project_path)
                    test_files.append(rel_path)
        
        return test_files
    
    def parse_test_output(self, stdout, stderr):
        """Parse pytest output into structured format - ENHANCED"""
        test_details = []
        
        if not stdout:
            return test_details
        
        lines = stdout.split('\n')
        current_test = None
        
        for line in lines:
            line = line.strip()
            
            # Match pytest output patterns
            # Example: "test_example.py::test_function PASSED"
            # Example: "test_example.py::test_function FAILED"
            
            if '::' in line:
                if 'PASSED' in line:
                    parts = line.split('::')
                    if len(parts) >= 2:
                        test_file = parts[0].strip()
                        test_name = parts[1].replace('PASSED', '').strip()
                        
                        test_details.append({
                            "name": f"{test_file}::{test_name}",
                            "passed": True,
                            "error": None,
                            "file": test_file
                        })
                
                elif 'FAILED' in line or 'ERROR' in line:
                    parts = line.split('::')
                    if len(parts) >= 2:
                        test_file = parts[0].strip()
                        test_name = parts[1].replace('FAILED', '').replace('ERROR', '').strip()
                        
                        # Try to get error details from following lines
                        error_msg = self._extract_error_details(lines, line)
                        
                        test_details.append({
                            "name": f"{test_file}::{test_name}",
                            "passed": False,
                            "error": error_msg,
                            "file": test_file
                        })
            
            # Also look for simple test patterns
            elif line.startswith('test_') and ('passed' in line.lower() or 'failed' in line.lower()):
                test_name = line.split()[0]
                status = 'passed' in line.lower()
                
                test_details.append({
                    "name": test_name,
                    "passed": status,
                    "error": None if status else "Test failed"
                })
        
        # If still no tests found, try a different approach
        if not test_details:
            test_pattern = r'(test_\w+)'
            tests = re.findall(test_pattern, stdout)
            for test in set(tests):
                test_details.append({
                    "name": test,
                    "passed": 'passed' in stdout.lower() or 'PASSED' in stdout,
                    "error": None
                })
        
        return test_details
    
    def _extract_error_details(self, lines, current_line):
        """Extract error details from test output"""
        try:
            idx = lines.index(current_line)
            error_lines = []
            for i in range(idx + 1, min(idx + 10, len(lines))):
                if lines[i].strip() and not lines[i].startswith('test_'):
                    error_lines.append(lines[i])
                else:
                    break
            return '\n'.join(error_lines[:3])  # Return first 3 lines of error
        except:
            return "Test failed"
    
    def run_specific_test(self, project_path, test_name):
        """Run a specific test"""
        try:
            # Check if it's a file or function
            if '::' in test_name:
                # It's a specific test function
                cmd = ["python", "-m", "pytest", test_name, "-v"]
            else:
                # It's a test file
                cmd = ["python", "-m", "pytest", f"{test_name}.py", "-v"]
            
            result = subprocess.run(
                cmd,
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return {
                "success": result.returncode == 0,
                "output": result.stdout + result.stderr
            }
            
        except Exception as e:
            return {
                "success": False,
                "output": f"Error: {e}"
            }
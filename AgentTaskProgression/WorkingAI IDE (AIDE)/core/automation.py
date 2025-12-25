import os
import time
import threading
import subprocess
import logging
from datetime import datetime

class AutomationManager:
    """
    Manages script validation, execution, and scheduling for Prometheus (PMT).
    """
    def __init__(self, app):
        self.app = app
        self.scheduled_jobs = {} # {id: {script, interval, last_run, next_run}}
        self.running = False
        self.monitor_thread = None
        
        # Setup automation logger
        self.logger = logging.getLogger("automation")
        handler = logging.FileHandler("automation.log")
        handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def start_scheduler(self):
        """Start the background scheduler thread"""
        if self.running: return
        self.running = True
        self.monitor_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.monitor_thread.start()
        self.logger.info("Scheduler started")

    def stop_scheduler(self):
        """Stop the scheduler"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
            
    def _scheduler_loop(self):
        while self.running:
            now = time.time()
            for job_id, job in list(self.scheduled_jobs.items()):
                if job['next_run'] <= now:
                    # Run job
                    self._run_job(job_id)
                    # Reschedule
                    job['last_run'] = now
                    job['next_run'] = now + job['interval']
            time.sleep(1) # Check every second

    def schedule_script(self, script_path, interval_seconds):
        """Schedule a script to run periodically"""
        if not os.path.exists(script_path):
            return None, "Script not found"
            
        job_id = f"job_{len(self.scheduled_jobs)}_{int(time.time())}"
        self.scheduled_jobs[job_id] = {
            "script": script_path,
            "interval": interval_seconds,
            "last_run": 0,
            "next_run": time.time(), # Run immediately/soon
            "created_at": datetime.now().isoformat()
        }
        self.logger.info(f"Scheduled job {job_id}: {script_path} every {interval_seconds}s")
        return job_id, "Scheduled successfully"

    def _run_job(self, job_id):
        """Execute a scheduled job"""
        job = self.scheduled_jobs.get(job_id)
        if not job: return
        
        script_path = job['script']
        self.logger.info(f"Running job {job_id}: {script_path}")
        
        # Pre-execution validation
        valid, issues = self.validate_script(script_path)
        if not valid:
            self.logger.error(f"Job {job_id} failed validation: {issues}")
            self._notify_failure(job_id, f"Validation failed: {issues}")
            return

        # Execution
        try:
            # Determine runner based on extension
            ext = os.path.splitext(script_path)[1].lower()
            cmd = []
            if ext == '.py':
                cmd = ["python", script_path]
            elif ext == '.js':
                cmd = ["node", script_path]
            else:
                # Fallback
                cmd = [script_path]
                
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                self.logger.info(f"Job {job_id} success. Output: {result.stdout[:100]}...")
            else:
                self.logger.error(f"Job {job_id} failed (code {result.returncode}). Error: {result.stderr}")
                self._notify_failure(job_id, f"Runtime error: {result.stderr}")
                
        except Exception as e:
            self.logger.error(f"Job {job_id} execution error: {e}")
            self._notify_failure(job_id, f"Execution exception: {e}")

    def validate_script(self, script_path):
        """
        Validate a script before execution.
        Returns: (bool, list_of_issues)
        """
        if not os.path.exists(script_path):
            return False, ["File not found"]
            
        # Use Core Linter if available
        if hasattr(self.app, 'linter'):
            issues = self.app.linter.lint_file(script_path)
            errors = [i for i in issues if i['type'] == 'error']
            if errors:
                return False, [e['message'] for e in errors]
        
        # Basic Syntax Check for Python if linter unavailable
        if script_path.endswith('.py'):
            try:
                with open(script_path, 'r', encoding='utf-8') as f:
                    compile(f.read(), script_path, 'exec')
            except SyntaxError as e:
                return False, [f"Syntax Error: {e.msg} at line {e.lineno}"]
                
        return True, []

    def _notify_failure(self, job_id, message):
        """Notify user/system of failure"""
        # Integrate with Notification system or just log
        print(f"[ALERT] Job {job_id} Failed: {message}")
        if hasattr(self.app, 'log_ai'):
            self.app.log_ai(f"⚠️ Automation Alert: Job {job_id} failed. {message}")

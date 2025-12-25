import os
import sys
import logging
import json
import subprocess
from datetime import datetime
import platform

# Configure logging for security audit
AUDIT_LOG_FILE = "security_audit.log"
logging.basicConfig(
    filename=AUDIT_LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class SecurityManager:
    """
    Manages security, access control, and audit logging for Prometheus (PMT).
    """
    def __init__(self, app):
        self.app = app
        self.admin_mode = self._check_admin_privileges()
        self.audit_log = []
        self._load_audit_log()
        
    def _check_admin_privileges(self):
        """Check if the current process has admin/root privileges"""
        try:
            if platform.system() == "Windows":
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                return os.geteuid() == 0
        except:
            return False

    def log_audit(self, action, details, status="SUCCESS"):
        """Log a security-relevant action"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details,
            "status": status,
            "user": os.getlogin()
        }
        self.audit_log.append(entry)
        logging.info(f"AUDIT: {json.dumps(entry)}")
        self._save_audit_log()
        
    def _load_audit_log(self):
        """Load audit log from file"""
        if os.path.exists(AUDIT_LOG_FILE):
            try:
                with open(AUDIT_LOG_FILE, 'r') as f:
                    # This is a simple append log, so we might need to parse line by line
                    # For now, just keep in memory what we log this session
                    pass
            except:
                pass

    def _save_audit_log(self):
        """Persist audit log (handled by logging module mostly)"""
        pass

    def require_admin(self):
        """Decorator or check for admin requirement"""
        if not self.admin_mode:
            raise PermissionError("This operation requires Administrator privileges.")
            
    def install_package(self, package_name):
        """Securely install a python package"""
        self.log_audit("INSTALL_PACKAGE", f"Attempting to install {package_name}")
        
        # Security check: prevent command injection (basic)
        if any(c in package_name for c in [';', '&', '|', '>', '<']):
            self.log_audit("INSTALL_PACKAGE", f"Blocked invalid package name: {package_name}", "BLOCKED")
            raise ValueError("Invalid package name")
            
        try:
            # self.require_admin() # Optional: pip usually works in user scope too
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
            self.log_audit("INSTALL_PACKAGE", f"Installed {package_name}", "SUCCESS")
            return True
        except subprocess.CalledProcessError as e:
            self.log_audit("INSTALL_PACKAGE", f"Failed to install {package_name}: {e}", "FAILURE")
            return False
        except PermissionError:
            self.log_audit("INSTALL_PACKAGE", f"Permission denied for {package_name}", "DENIED")
            return False

    def run_privileged_command(self, command):
        """Run a system command with potential elevation (if app is admin)"""
        self.require_admin()
        self.log_audit("RUN_PRIVILEGED", f"Command: {command}")
        
        # In a real scenario, we would be very careful here.
        # For this "IDE", we assume the user trusts the agent.
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            self.log_audit("RUN_PRIVILEGED", "Command executed", "SUCCESS" if result.returncode == 0 else "FAILURE")
            return result.stdout + result.stderr
        except Exception as e:
            self.log_audit("RUN_PRIVILEGED", f"Execution error: {e}", "ERROR")
            return str(e)

import os
import shutil
import time
from datetime import datetime

class BackupManager:
    def __init__(self, project_path):
        self.project_path = project_path
        self.backup_dir = os.path.join(project_path, ".ai_backups")
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
            
    def create_backup(self, file_path):
        """Create a backup of a file before modification."""
        if not os.path.exists(file_path):
            return None
            
        try:
            rel_path = os.path.relpath(file_path, self.project_path)
            # Create subdirectories in backup_dir if needed
            backup_file_dir = os.path.join(self.backup_dir, os.path.dirname(rel_path))
            if not os.path.exists(backup_file_dir):
                os.makedirs(backup_file_dir)
                
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{os.path.basename(file_path)}.{timestamp}.bak"
            backup_path = os.path.join(backup_file_dir, backup_name)
            
            shutil.copy2(file_path, backup_path)
            return backup_path
        except Exception as e:
            print(f"Error creating backup for {file_path}: {e}")
            return None

    def restore_backup(self, original_path, backup_path):
        """Restore a file from a backup."""
        try:
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, original_path)
                return True
        except Exception as e:
            print(f"Error restoring backup for {original_path}: {e}")
        return False

    def get_latest_backups(self, count=5):
        """Get the latest backup sessions."""
        # This is a simplified version. A "session" could be all backups within a small time window.
        pass

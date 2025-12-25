import json
import os
import threading
import time
from datetime import datetime

class PlanningSystem:
    """
    Centralized Planning System for Prometheus (PMT).
    Manages the state of the project, user intentions, and agent activities.
    Syncs with 'planning.json' in real-time.
    """
    def __init__(self, app):
        self.app = app
        self.lock = threading.RLock()
        self.planning_file = "planning.json"
        self.auto_save = self.app.settings.get("auto_save_planning", True)
        
        # Undo/Redo Stacks (Limited to 20 steps)
        self.undo_stack = []
        self.redo_stack = []
        
        # Default State
        self.state = {
            "project_name": "Unknown",
            "last_updated": None,
            "version": 1,
            "status": "active",
            "goals": [], # High level goals
            "tasks": [], # Specific actionable items
            "agents": {}, # Agent states {name: {status, current_task}}
            "context": {} # Shared context/memory
        }
        
        # Load existing
        self.load_state()

    def _push_undo(self):
        """Push current state to undo stack before a change"""
        import copy
        self.undo_stack.append(copy.deepcopy(self.state))
        if len(self.undo_stack) > 20:
            self.undo_stack.pop(0)
        self.redo_stack.clear() # Clear redo stack on new action

    def undo(self):
        """Revert to previous state"""
        if not self.undo_stack:
            return False
        import copy
        self.redo_stack.append(copy.deepcopy(self.state))
        self.state = self.undo_stack.pop()
        self.save_state(force=True)
        return True

    def redo(self):
        """Re-apply a reverted state"""
        if not self.redo_stack:
            return False
        import copy
        self.undo_stack.append(copy.deepcopy(self.state))
        self.state = self.redo_stack.pop()
        self.save_state(force=True)
        return True
        
    def _get_path(self):
        if self.app.project_path:
            return os.path.join(self.app.project_path, self.planning_file)
        return None

    def validate_task(self, task):
        """Validate task data structure"""
        required = ["description", "status"]
        for field in required:
            if field not in task or not task[field]:
                return False, f"Missing required field: {field}"
        return True, None

    def load_state(self):
        """Load state from JSON file"""
        path = self._get_path()
        if path and os.path.exists(path):
            with self.lock:
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # Merge with default structure to ensure valid schema
                        self.state.update(data)
                except Exception as e:
                    print(f"Failed to load planning file: {e}")

    def save_state(self, force=False):
        """Save current state to JSON file"""
        if not self.auto_save and not force:
            return
            
        path = self._get_path()
        if not path: return
        
        with self.lock:
            self.state["last_updated"] = datetime.now().isoformat()
            self.state["version"] += 1
            try:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                # Validate all tasks before saving
                for task in self.state["tasks"]:
                    valid, err = self.validate_task(task)
                    if not valid:
                        print(f"Task validation failed: {err}")
                
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(self.state, f, indent=2)
            except Exception as e:
                print(f"Failed to save planning file: {e}")

    def update_goal(self, goal_id, status=None, description=None):
        """Update or add a high-level goal"""
        with self.lock:
            self._push_undo()
            # Find existing
            found = False
            for g in self.state["goals"]:
                if g["id"] == goal_id:
                    if status: g["status"] = status
                    if description: g["description"] = description
                    g["updated_at"] = datetime.now().isoformat()
                    found = True
                    break
            
            if not found and description:
                self.state["goals"].append({
                    "id": goal_id,
                    "description": description,
                    "status": status or "pending",
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                })
            
            self.save_state()

    def add_task(self, description, agent=None, priority="medium"):
        """Add a new actionable task"""
        with self.lock:
            self._push_undo()
            task = {
                "id": f"task_{int(time.time())}_{len(self.state['tasks'])}",
                "description": description,
                "assigned_to": agent,
                "priority": priority,
                "status": "pending",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "status_history": [{"status": "pending", "timestamp": datetime.now().isoformat()}]
            }
            self.state["tasks"].append(task)
            self.save_state()
            return task["id"]

    def update_task_status(self, task_id, status, notes=None):
        """Update a task's status with history tracking"""
        with self.lock:
            self._push_undo()
            for t in self.state["tasks"]:
                if t["id"] == task_id:
                    if t["status"] != status:
                        t["status"] = status
                        t["updated_at"] = datetime.now().isoformat()
                        t["status_history"].append({
                            "status": status,
                            "timestamp": datetime.now().isoformat(),
                            "notes": notes
                        })
                    break
            self.save_state()

    def todo_write(self, todos, merge=True):
        """
        Implementation of the TodoWrite tool for AI agents.
        Updates tasks in the planning system.
        """
        with self.lock:
            self._push_undo()
            if not merge:
                # If not merging, we replace existing tasks with new ones
                # but we keep completed ones if they aren't in the new list?
                # Actually, let's just clear and replace for simplicity if merge=False
                self.state["tasks"] = []
            
            for todo in todos:
                # todo: {id, content, status, priority}
                found = False
                for t in self.state["tasks"]:
                    if t["id"] == todo["id"]:
                        t["description"] = todo.get("content", t["description"])
                        if "status" in todo and t["status"] != todo["status"]:
                            t["status"] = todo["status"]
                            t["status_history"].append({
                                "status": todo["status"],
                                "timestamp": datetime.now().isoformat()
                            })
                        t["priority"] = todo.get("priority", t["priority"])
                        t["updated_at"] = datetime.now().isoformat()
                        found = True
                        break
                
                if not found:
                    self.state["tasks"].append({
                        "id": todo["id"],
                        "description": todo["content"],
                        "status": todo["status"],
                        "priority": todo["priority"],
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat(),
                        "status_history": [{"status": todo["status"], "timestamp": datetime.now().isoformat()}]
                    })
            self.save_state()
            return True

    def update_agent_status(self, agent_name, status, current_task=None):
        """Update agent activity tracking"""
        with self.lock:
            self.state["agents"][agent_name] = {
                "status": status,
                "current_task": current_task,
                "last_active": datetime.now().isoformat()
            }
            self.save_state()

    def get_pending_tasks(self, agent_name=None):
        """Get tasks that are pending"""
        with self.lock:
            tasks = [t for t in self.state["tasks"] if t["status"] == "pending"]
            if agent_name:
                tasks = [t for t in tasks if t.get("assigned_to") in [agent_name, None]]
            return tasks

    def complete_task(self, task_id, result=None):
        """Mark task as complete"""
        with self.lock:
            for t in self.state["tasks"]:
                if t["id"] == task_id:
                    t["status"] = "completed"
                    t["completed_at"] = datetime.now().isoformat()
                    t["result"] = result
                    break
            self.save_state()

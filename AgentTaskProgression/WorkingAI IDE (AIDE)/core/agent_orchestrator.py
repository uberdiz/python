"""
Agent Orchestrator - Manages agent lifecycle and inter-agent communication
"""
import threading
import queue
from datetime import datetime
from collections import defaultdict

class MessageBus:
    """Pub/sub message bus for agent communication"""
    
    def __init__(self):
        self.subscribers = defaultdict(list)  # topic -> [callbacks]
        self.message_log = []
        self._lock = threading.Lock()
        
    def subscribe(self, topic, callback):
        """Subscribe to a topic"""
        with self._lock:
            self.subscribers[topic].append(callback)
            
    def unsubscribe(self, topic, callback):
        """Unsubscribe from a topic"""
        with self._lock:
            if callback in self.subscribers[topic]:
                self.subscribers[topic].remove(callback)
                
    def publish(self, topic, message):
        """Publish message to topic"""
        with self._lock:
            self.message_log.append({
                "topic": topic,
                "message": message,
                "timestamp": datetime.now().isoformat()
            })
            for callback in self.subscribers[topic]:
                try:
                    callback(message)
                except Exception as e:
                    print(f"MessageBus error: {e}")


class AgentOrchestrator:
    """Manages agent lifecycle and task distribution"""
    
    def __init__(self, app):
        self.app = app
        self.agents = {}  # name -> agent instance
        self.message_bus = MessageBus()
        self.task_queue = queue.PriorityQueue()
        self.logs = []
        self._running = False
        self._thread = None
        
        # Callbacks for UI updates
        self.on_agent_status_change = None
        self.on_log = None
        self.agent_monitor = None  # Reference to AgentMonitor window
        
        # Approval gate system
        self.approval_required = True  # User must approve before agents execute
        self.pending_approvals = []  # Tasks waiting for approval
        self.on_approval_needed = None  # Callback when approval dialog needed
        self.shared_history = []  # Global conversation history for current agent group
        self.current_group_name = None
        # Optional WebSocket broadcasting
        self._ws_clients = set()
        self._ws_server_thread = None
        try:
            self.start_ws_server()
        except Exception:
            pass
        
    def register_agent(self, agent):
        """Register an agent with the orchestrator"""
        agent.orchestrator = self
        self.agents[agent.name] = agent
        self.log(f"Agent registered: {agent.name} ({agent.role})")
        
        # Subscribe agent to its own topic
        self.message_bus.subscribe(agent.name, lambda msg: agent.queue_message(msg["from"], msg["content"]))
        
    def unregister_agent(self, agent_name):
        """Remove an agent"""
        if agent_name in self.agents:
            agent = self.agents[agent_name]
            agent.stop()
            del self.agents[agent_name]
            self.log(f"Agent unregistered: {agent_name}")
            
    def start_all(self):
        """Start all registered agents"""
        self._running = True
        for agent in self.agents.values():
            agent.start()
        self.log("All agents started")
        
    def stop_all(self):
        """Stop all agents"""
        self._running = False
        for agent in self.agents.values():
            agent.stop()
        self.log("All agents stopped")
        
    def route_message(self, from_agent, to_agent, content):
        """Route message between agents"""
        message = {
            "from": from_agent,
            "to": to_agent,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        self.shared_history.append(message)
        if len(self.shared_history) > 100:
            self.shared_history.pop(0)
        # Persist history per group if configured
        try:
            self._persist_shared_history()
        except Exception as e:
            self.log(f"History persist error: {e}")
        
        self.log(f"{from_agent} -> {to_agent}: {content[:50]}...")
        # Broadcast snapshot to websocket clients
        try:
            self.broadcast_status_snapshot()
        except Exception:
            pass
        
        # Direct message to specific agent
        if to_agent in self.agents:
            self.message_bus.publish(to_agent, message)
        elif to_agent == "fixer" and "fixer" not in self.agents:
            # Fallback to coder if fixer is missing
            self.log("Fixer agent not found. Falling back to Coder.")
            fallback_coder = self._find_best_agent_by_role("coder")
            if fallback_coder:
                message["to"] = fallback_coder.name
                self.message_bus.publish(fallback_coder.name, message)
            else:
                self.log("No fallback Coder found.")
        else:
            # Broadcast to all if no specific target
            for name in self.agents:
                if name != from_agent:
                    self.message_bus.publish(name, message)

    def handle_error(self, error_msg, context=None):
        """Handle an unresolved error by routing it to the fixer or best available agent"""
        self.log(f"Handling unresolved error: {error_msg[:100]}...")
        
        full_context = f"ERROR: {error_msg}\n"
        if context:
            full_context += f"CONTEXT: {context}\n"
        
        # Add debugging info if available
        if hasattr(self.app, 'project_path'):
            full_context += f"PROJECT_PATH: {self.app.project_path}\n"

        # Try to route to fixer first
        if "fixer" in self.agents:
            self.route_message("orchestrator", "fixer", full_context)
            return "routed_to_fixer"
        
        # Fallback to most qualified coder
        best_coder = self._find_best_agent_by_role("coder")
        if best_coder:
            self.log(f"No fixer agent available. Routing to coder: {best_coder.name}")
            self.route_message("orchestrator", best_coder.name, full_context)
            return f"routed_to_{best_coder.name}"
            
        self.log("No suitable agent found to handle the error.")
        return "no_agent_available"

    def _find_best_agent_by_role(self, role):
        """Find the best available agent for a given role"""
        candidates = [a for a in self.agents.values() if a.role.lower() == role.lower()]
        if not candidates:
            return None
        # Simple heuristic: pick the one with the shortest queue
        return min(candidates, key=lambda a: a.message_queue.qsize() if hasattr(a, 'message_queue') else 999)
                    
    def submit_task(self, task, priority=5):
        """Submit a task to the queue (lower priority = higher)"""
        self.task_queue.put((priority, task))
        self.log(f"Task submitted: {task.get('type', 'unknown')}")
        
    def get_agent_statuses(self):
        """Get status of all agents"""
        return {name: agent.to_dict() for name, agent in self.agents.items()}
        
    def log(self, message):
        """Log orchestrator activity"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] [Orchestrator] {message}"
        self.logs.append(entry)
        print(entry)
        
        # Notify UI if callback registered
        if self.on_log:
            try:
                self.on_log(entry)
            except:
                pass
                
        # Notify agent monitor if connected
        if self.agent_monitor:
            try:
                self.agent_monitor.append_log("Orchestrator", message)
            except:
                pass
                
    def get_logs(self, last_n=50):
        """Get recent logs"""
        return self.logs[-last_n:]
        
    def create_agent(self, agent_class, name, role, model_provider, model_name):
        """Factory method to create and register an agent"""
        agent = agent_class(name, role, model_provider, model_name, self)
        self.register_agent(agent)
        return agent

    def create_agent_by_role(self, name, role, provider, model):
        """Helper to create agent by role string"""
        # Validate model enforcement - ensure we check against the specific provider
        if hasattr(self.app, 'ai_manager'):
            if not self.app.ai_manager.validate_model(model, provider):
                allowed = self.app.ai_manager.get_allowed_models(provider)
                if allowed:
                    self.log(f"Warning: Model '{model}' not allowed for provider '{provider}'. Switching to '{allowed[0]}'.")
                    model = allowed[0]
                else:
                    self.log(f"Warning: Model '{model}' not allowed for provider '{provider}', and no allowed models found.")

        agent_classes = {
            "planner": ("agents.planner_agent", "PlannerAgent"),
            "coder": ("agents.coder_agent", "CoderAgent"),
            "image_agent": ("agents.image_agent", "ImageAgent"),
            "gui_coder": ("agents.gui_coder_agent", "GUICoderAgent"),
            "tester": ("agents.tester_agent", "TesterAgent"),
            "fixer": ("agents.fixer_agent", "FixerAgent")
        }
        
        try:
            module_name, class_name = agent_classes.get(role, ("agents.planner_agent", "PlannerAgent"))
            module = __import__(module_name, fromlist=[class_name])
            agent_class = getattr(module, class_name)
            
            # Check and pull Ollama model if needed
            if provider == "ollama" and hasattr(self.app, 'ai_manager'):
                if not self.app.ai_manager.is_ollama_model_downloaded(model):
                    self.log(f"System: Ollama model '{model}' not found. Starting automatic pull...")
                    
                    def auto_pull():
                        def progress_cb(s):
                            st = s.get("status", "Pulling")
                            if "completed" in s and "total" in s:
                                p = (s["completed"] / s["total"]) * 100
                                st = f"{p:.1f}% - {st}"
                            self.log(f"System [Pull {model}]: {st}")
                            
                        if self.app.ai_manager.pull_ollama_model(model, progress_cb):
                            self.log(f"System: Successfully pulled Ollama model '{model}'. Agent '{name}' is ready.")
                        else:
                            self.log(f"Error: Failed to pull Ollama model '{model}'. Agent '{name}' may fail to run.")

                    import threading
                    threading.Thread(target=auto_pull, daemon=True).start()

            agent = agent_class(name=name, role=role, model_provider=provider, model_name=model, orchestrator=self)
            self.register_agent(agent)
            return agent
        except Exception as e:
            self.log(f"Error creating agent {name}: {e}")
            return None

    def save_config(self, group_name="default"):
        """Save current agents to app settings"""
        config = []
        for name, agent in self.agents.items():
            config.append({
                "name": agent.name,
                "role": agent.role,
                "provider": agent.model_provider,
                "model": agent.model_name
            })
            
        if "agent_groups" not in self.app.settings:
            self.app.settings["agent_groups"] = {}
            
        self.app.settings["agent_groups"][group_name] = config
        self.app.save_settings(self.app.settings)
        self.log(f"Config '{group_name}' saved to settings.")

        # Track current group and persist its shared chat history
        self.current_group_name = group_name
        try:
            self._persist_shared_history()
        except Exception as e:
            self.log(f"Error saving shared history for group '{group_name}': {e}")
        try:
            self.broadcast_status_snapshot()
        except Exception:
            pass

        # Align allowed models with this group's agents
        try:
            models = sorted({item["model"] for item in config if item.get("model")})
            if models:
                self.app.settings["allowed_models"] = ",".join(models)
                self.app.save_settings(self.app.settings)
                self.log(f"Allowed models updated from group '{group_name}': {models}")
                if hasattr(self.app, "ai_panel") and hasattr(self.app.ai_panel, "update_model_list"):
                    self.app.ai_panel.update_model_list()
        except Exception as e:
            self.log(f"Error updating allowed models from config: {e}")

    def load_config(self, group_name="default"):
        """Load agents from app settings"""
        groups = self.app.settings.get("agent_groups", {})
        if group_name not in groups:
            self.log(f"Config '{group_name}' not found.")
            return False
            
        config = groups[group_name]
        self.stop_all()
        # Clear existing
        names = list(self.agents.keys())
        for name in names:
            self.unregister_agent(name)
            
        for item in config:
            self.create_agent_by_role(item["name"], item["role"], item["provider"], item["model"])
            
        self.log(f"Config '{group_name}' loaded.")
        self.current_group_name = group_name
        # Load shared chat history for this group
        try:
            self.shared_history = self._load_shared_history()
            self.log(f"Loaded shared history for group '{group_name}' ({len(self.shared_history)} messages)")
            # Reflect in chat UI if available
            if hasattr(self.app, "ai_panel") and hasattr(self.app.ai_panel, "set_chat_history"):
                self.app.ai_panel.set_chat_history(self.shared_history)
        except Exception as e:
            self.log(f"Error loading shared history for group '{group_name}': {e}")
        try:
            self.broadcast_status_snapshot()
        except Exception:
            pass
        
        # Enforce allowed models derived from the loaded group
        try:
            models = sorted({item["model"] for item in config if item.get("model")})
            if models:
                self.app.settings["allowed_models"] = ",".join(models)
                if hasattr(self.app, "save_settings"):
                    self.app.save_settings(self.app.settings)
                self.log(f"Allowed models enforced from group '{group_name}': {models}")
                if hasattr(self.app, "ai_panel") and hasattr(self.app.ai_panel, "update_model_list"):
                    self.app.ai_panel.update_model_list()
        except Exception as e:
            self.log(f"Error enforcing allowed models after load: {e}")
        
        return True

    def _history_path(self):
        """Compute path for shared history file for current group"""
        import os
        base = None
        try:
            base = self.app.project_path if getattr(self.app, 'project_path', None) else os.path.expanduser("~")
        except Exception:
            import os as _os
            base = _os.path.expanduser("~")
        name = self.current_group_name or "default"
        return os.path.join(base, f".agent_history_{name}.json")

    def _persist_shared_history(self):
        """Persist shared history to disk for the current group"""
        import json, os
        path = self._history_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.shared_history, f, indent=2)

    def _load_shared_history(self):
        """Load shared history from disk for the current group"""
        import json, os
        path = self._history_path()
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Validate minimal schema
                    if isinstance(data, list):
                        return [
                            {
                                "from": item.get("from", "unknown"),
                                "to": item.get("to", "unknown"),
                                "content": item.get("content", ""),
                                "timestamp": item.get("timestamp", datetime.now().isoformat())
                            } for item in data
                        ]
            except Exception as e:
                self.log(f"Failed to read history file: {e}")
        return []

    # --- WebSocket Broadcasting (optional) ---
    def start_ws_server(self):
        """Start a lightweight websocket server if library available"""
        import threading
        try:
            import asyncio, json as _json
            try:
                import websockets
            except ImportError:
                websockets = None
        except Exception:
            return
        async def handler(websocket, path):
            self._ws_clients.add(websocket)
            try:
                # Send initial snapshot
                await websocket.send(_json.dumps(self.get_agent_snapshot()))
                async for _ in websocket:
                    # Clients don't send commands; ignore
                    pass
            except Exception:
                pass
            finally:
                try:
                    self._ws_clients.remove(websocket)
                except Exception:
                    pass
        async def run():
            try:
                server = await websockets.serve(handler, '127.0.0.1', 8765)
                await server.wait_closed()
            except Exception:
                pass
        def start():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(run())
            except Exception:
                pass
        if not self._ws_server_thread:
            t = threading.Thread(target=start, daemon=True)
            t.start()
            self._ws_server_thread = t

    def get_agent_snapshot(self):
        """Return current agent statuses for broadcasting"""
        snapshot = {
            "group": self.current_group_name or "default",
            "agents": []
        }
        try:
            import json as _json
            for name, agent in self.agents.items():
                item = {
                    "name": name,
                    "role": getattr(agent, 'role', ''),
                    "status": getattr(agent, 'status', 'idle'),
                    "queue": agent.message_queue.qsize() if hasattr(agent, 'message_queue') else 0,
                    "last": agent.history[-1]['content'][:120] if getattr(agent, 'history', []) else ""
                }
                snapshot["agents"].append(item)
        except Exception:
            pass
        return snapshot

    def broadcast_status_snapshot(self):
        """Broadcast agent snapshot to all websocket clients"""
        try:
            import asyncio, json as _json
            if not self._ws_clients:
                return
            data = _json.dumps(self.get_agent_snapshot())
            async def _send_all():
                tasks = []
                for ws in list(self._ws_clients):
                    try:
                        tasks.append(ws.send(data))
                    except Exception:
                        pass
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)
            loop = asyncio.get_event_loop()
            if loop and loop.is_running():
                asyncio.run_coroutine_threadsafe(_send_all(), loop)
        except Exception:
            pass
        
    def run_workflow(self, workflow_name, context):
        """Execute a predefined workflow"""
        self.log(f"Starting workflow: {workflow_name}")
        
        # Check if approval is required
        if self.approval_required:
            task = {
                "workflow": workflow_name,
                "context": context,
                "status": "pending_approval"
            }
            self.pending_approvals.append(task)
            self.log(f"Workflow queued for approval: {workflow_name}")
            
            # Trigger approval dialog
            if self.on_approval_needed:
                self.on_approval_needed(task)
            return "pending_approval"
        
        return self._execute_workflow(workflow_name, context)
        
    def _execute_workflow(self, workflow_name, context):
        """Actually execute the workflow (after approval)"""
        if workflow_name == "plan_and_code":
            return self._workflow_plan_and_code(context)
        elif workflow_name == "image_to_gui":
            return self._workflow_image_to_gui(context)
        elif workflow_name == "test_and_fix":
            return self._workflow_test_and_fix(context)
        else:
            self.log(f"Unknown workflow: {workflow_name}")
            return None
            
    def approve_task(self, task_index=0):
        """Approve a pending task"""
        if task_index < len(self.pending_approvals):
            task = self.pending_approvals.pop(task_index)
            task["status"] = "approved"
            self.log(f"Approved workflow: {task['workflow']}")
            return self._execute_workflow(task["workflow"], task["context"])
        return None
        
    def reject_task(self, task_index=0):
        """Reject a pending task"""
        if task_index < len(self.pending_approvals):
            task = self.pending_approvals.pop(task_index)
            self.log(f"Rejected workflow: {task['workflow']}")
        return None
        
    def get_pending_approvals(self):
        """Get list of pending approvals"""
        return self.pending_approvals.copy()
        
    def toggle_approval_gate(self, enabled):
        """Enable/disable approval requirement"""
        self.approval_required = enabled
        state = "enabled" if enabled else "disabled"
        self.log(f"Approval gate {state}")
            
    def _workflow_plan_and_code(self, context):
        """Planner -> Coder workflow"""
        if "planner" in self.agents and "coder" in self.agents:
            # Send task to planner
            self.route_message("user", "planner", f"Create a plan for: {context.get('description', '')}")
        return True
        
    def _workflow_image_to_gui(self, context):
        """Image Agent -> GUI Coder workflow"""
        if "image_agent" in self.agents and "gui_coder" in self.agents:
            # Image agent analyzes first
            image_path = context.get("image_path", "")
            self.route_message("user", "image_agent", f"Analyze this UI mockup: {image_path}")
        return True
        
    def _workflow_test_and_fix(self, context):
        """Tester -> Fixer/Coder loop"""
        if "tester" in self.agents:
            target = context.get('file_path', '')
            self.route_message("user", "tester", f"Run tests on: {target}")
            
            # If tests fail, the tester will broadcast failures.
            # We can also explicitly link them if needed, but the current 
            # message bus system allows agents to react to broadcasted failures.
        elif "fixer" in self.agents:
            # If no tester, but we have a fixer, maybe we just want to fix a known error
            error_log = context.get('error_log', '')
            if error_log:
                self.route_message("user", "fixer", f"ERROR: {error_log}")
        return True

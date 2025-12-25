"""
Chat Agent - Optimized for speed, correctness, and agent coordination
"""
import os
import re
import difflib
import subprocess
import json
import threading
import time
import logging
from concurrent.futures import ThreadPoolExecutor

# Set up logging
logger = logging.getLogger(__name__)

# Global caches for performance optimization
_INTENT_CACHE = {}
_CACHE_LOCK = threading.Lock()

# --- AI IDE CHAT SYSTEM PROMPT (Agent Workflow Optimizer) ---
SYSTEM_PROMPT = """
You are an AI systems engineer embedded inside a custom AI IDE. 
Your job is to improve how the IDE completes tasks: faster execution, fewer errors, better agent coordination, and deterministic results. Every response must optimize for speed, correctness, and production safety.

Core Rules (Hard Constraints)
- Prefer structured output over prose
- Prefer small, fast models unless escalation is required
- Never hallucinate — escalate or re-plan instead
- Only rewrite entire files if it's the most efficient way to apply changes (e.g. major UI updates)
- No chain-of-thought or internal reasoning in outputs

Mandatory Task Flow
1. Parse intent
2. Decompose into tasks (Planner)
3. Execute tasks (parallel where possible)
4. Validate results
5. Apply patches/diffs
6. Final sanity check
7. Return a short user summary (≤5 lines)

Code Interaction Rules
- Prefer patches / unified diffs
- Always reference file paths and symbols
- Touch the smallest possible surface area
- If unsure, ask for clarification instead of guessing

Failure Handling
- If any agent is uncertain → escalate
- If any agent fails validation twice → re-plan from scratch
"""

def chat_agent(message, api_url, model, api_provider="openai", token=None, context=None, execute_actions=True, conversation_history=None, on_tasks_update=None, on_phase_update=None, stop_event=None):
    """Enhanced chat agent following the Agent Workflow Optimizer rules"""
    from core.llm import call_llm
    
    if stop_event and stop_event.is_set():
        return {"response": "Task cancelled.", "status": "cancelled"}
    
    # Detect intent
    modification_keywords = ["modify", "change", "update", "edit", "fix", "add", "remove", "make", "set", "refactor"]
    
    # Clean message for prompts (remove large base64 data if present)
    clean_message = message
    if "data:image" in message:
        # Keep the text but remove the base64 part
        clean_message = re.sub(r'data:image/[^;]+;base64,[^ \n\r]+', '[IMAGE_DATA]', message)
    
    is_modification = any(keyword in message.lower() for keyword in modification_keywords) or "IMAGE_ANALYSIS_COMPLETE" in message or "REVISED_TASK" in message
    
    command_keywords = ["run", "execute", "terminal", "shell", "command", "pip", "python", "npm", "git"]
    is_command = any(keyword in message.lower() for keyword in command_keywords)
    
    if is_modification and context:
        # Before modification, check if we need to search or read more context
        if "calculator" in message.lower() and not any("calculator.py" in f.lower() for f in context.get("open_files", [])):
            # Force read calculator.py if it exists
            calc_path = os.path.join(context.get("project_path", ""), "calculator.py")
            if os.path.exists(calc_path):
                context["current_file"] = calc_path
                try:
                    with open(calc_path, 'r', encoding='utf-8') as f:
                        context["current_content"] = f.read()
                except: pass
        
        return handle_modification_request(clean_message, context, api_url, model, api_provider, token, execute_actions, on_tasks_update, on_phase_update, stop_event=stop_event)
    elif is_command and not is_modification:
        return handle_command_request(clean_message, context, api_url, model, api_provider, token, execute_actions, stop_event=stop_event)
    else:
        # Structured General Chat
        prompt = f"{SYSTEM_PROMPT}\n\nContext: {context if context else 'No context'}\nUser: {message}"
        response = call_llm(prompt, api_url, model, api_provider, token, stop_event=stop_event, system_prompt=SYSTEM_PROMPT)
        
        return {
            "response": response,
            "actions_performed": [],
            "requires_approval": False
        }

def verify_code_syntax(code, filepath):
    """Verify syntax of Python code by compiling it"""
    if not filepath.endswith('.py'):
        return True, ""
    try:
        compile(code, filepath, 'exec')
        return True, ""
    except SyntaxError as e:
        error_msg = f"Syntax error: {e.msg} at line {e.lineno}"
        if e.text:
            error_msg += f"\nCode: {e.text.strip()}"
        return False, error_msg
    except Exception as e:
        return False, str(e)

def perform_agent_search(query, project_path):
    """Helper for the agent to search the codebase"""
    try:
        results = []
        for root, dirs, files in os.walk(project_path):
            if any(ignored in root for ignored in ['.venv', '.git', '__pycache__', 'node_modules']):
                continue
            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.html', '.css', '.json')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if query.lower() in content.lower():
                                rel_path = os.path.relpath(file_path, project_path)
                                results.append(f"File: {rel_path}")
                    except:
                        continue
        if not results:
            return f"No matches found for '{query}'."
        return "Search Results:\n" + "\n".join(results[:15]) + ("\n...and more" if len(results) > 15 else "")
    except Exception as e:
        return f"Search error: {e}"

def apply_patch(filepath, original_content, patch_text, dry_run=False, backup_mgr=None):
    """Apply a unified diff patch or full code to a file with robust handling"""
    try:
        if not dry_run and backup_mgr:
            backup_mgr.create_backup(filepath)
            
        # Ensure patch_text is clean
        patch_text = re.sub(r'```diff\n|```python\n|```\n|```', '', patch_text).strip()
        
        # Determine if this is a patch or full content
        is_unified_diff = "--- a/" in patch_text or "+++" in patch_text or "@@" in patch_text
        
        # If it doesn't look like a patch, assume it's the full code
        if not is_unified_diff:
            # SAFETY CHECK: If the patch is very short but the file is large, 
            # and it doesn't look like a complete file (e.g., no imports, no class/def at start),
            # it might be a snippet that was intended to be a patch but lacks headers.
            # However, for now, we follow the Coder's instruction to provide FULL logic.
            modified_content = patch_text
            if not modified_content.strip() and original_content.strip():
                return {"success": False, "error": "Patch resulted in empty file. Rejecting."}
            if dry_run:
                return {"success": True, "modified_content": modified_content}
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            return {"success": True, "modified_content": modified_content}

        # It's a unified diff
        lines = original_content.splitlines(keepends=True)
        # Split into chunks based on @@
        chunks = re.split(r'(@@ -\d+,?\d* \+\d+,?\d* @@)', patch_text)
        
        if len(chunks) < 3:
            return {"success": False, "error": "Malformed patch: could not find chunk headers."}
            
        result_lines = list(lines)
        offset = 0 # Track how much the file length has changed
        
        for i in range(1, len(chunks), 2):
            header = chunks[i]
            content = chunks[i+1] if i+1 < len(chunks) else ""
            
            match = re.search(r'@@ -(\d+),?(\d*) \+(\d+),?(\d*) @@', header)
            if not match: continue
            
            orig_start = int(match.group(1))
            
            patch_chunk_lines = content.splitlines(keepends=True)
            search_lines = []
            for line in patch_chunk_lines:
                if line.startswith(' ') or line.startswith('-'):
                    search_lines.append(line[1:])
            
            pos = orig_start - 1 + offset
            match_found = False
            
            # Fuzzy matching
            search_area_start = max(0, pos - 50)
            search_area_end = min(len(result_lines), pos + 50 + len(search_lines))
            
            for j in range(search_area_start, search_area_end - len(search_lines) + 1):
                potential_match = result_lines[j:j+len(search_lines)]
                if all(potential_match[k].strip() == search_lines[k].strip() for k in range(len(search_lines))):
                    pos = j
                    match_found = True
                    break
            
            if not match_found:
                for j in range(len(result_lines) - len(search_lines) + 1):
                    potential_match = result_lines[j:j+len(search_lines)]
                    if all(potential_match[k].strip() == search_lines[k].strip() for k in range(len(search_lines))):
                        pos = j
                        match_found = True
                        break
            
            if match_found:
                new_chunk_lines = []
                for line in patch_chunk_lines:
                    if line.startswith('+'):
                        new_chunk_lines.append(line[1:])
                    elif line.startswith(' '):
                        new_chunk_lines.append(line[1:])
                
                old_len = len(search_lines)
                result_lines[pos:pos+old_len] = new_chunk_lines
                offset += len(new_chunk_lines) - old_len
            else:
                return {"success": False, "error": f"Could not find match for patch chunk at line {orig_start}"}
        
        modified_content = "".join(result_lines)
        if not modified_content.strip() and original_content.strip():
            return {"success": False, "error": "Patch resulted in empty file."}
            
        if dry_run:
            return {"success": True, "modified_content": modified_content}
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        return {"success": True, "modified_content": modified_content}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def handle_modification_request(message, context, api_url, model, api_provider, token, execute_actions=True, on_tasks_update=None, on_phase_update=None, stop_event=None):
    """Handle file modification requests using a 6-phase multi-agent pipeline"""
    from core.llm import call_llm
    from utils.backup import BackupManager
    
    # Check for cancellation
    if stop_event and stop_event.is_set():
        return {"response": "Task cancelled by user.", "status": "cancelled"}

    current_file = context.get("current_file")
    project_path = context.get("project_path")
    
    backup_mgr = None
    if project_path:
        backup_mgr = BackupManager(project_path)
    open_files = context.get("open_files", [])
    
    if not project_path or not os.path.exists(project_path):
        return {"response": "No project path provided.", "actions_performed": [], "requires_approval": False}
    
    project_tree = context.get("project_tree", [])
    target_file_hint = current_file or (open_files[0] if open_files else os.path.join(project_path, "main.py"))
    
    # Use current file if available, otherwise check open files, then default to main.py
    if current_file and os.path.exists(current_file):
        try:
            with open(current_file, 'r', encoding='utf-8') as f:
                current_content = f.read()
        except Exception as e:
            return {"response": f"Error reading file: {e}", "actions_performed": [], "requires_approval": False}
    elif open_files and any(os.path.exists(f) for f in open_files):
        # Prefer files mentioned in message if any
        found_mentioned = False
        for f in open_files:
            if os.path.basename(f).lower() in message.lower():
                current_file = f
                found_mentioned = True
                break
        if not found_mentioned:
            current_file = open_files[0]
            
        try:
            with open(current_file, 'r', encoding='utf-8') as f:
                current_content = f.read()
        except:
            current_content = ""
    else:
        current_content = ""
        # Look for keywords in message and project tree to guess the file
        if "calculator" in message.lower():
            # Check project tree first
            calc_files = [f for f in project_tree if "calculator.py" in f.lower()]
            if calc_files:
                current_file = calc_files[0] if os.path.isabs(calc_files[0]) else os.path.join(project_path, calc_files[0])
            else:
                current_file = os.path.join(project_path, "calculator.py")
        elif "app" in message.lower():
            app_files = [f for f in project_tree if "app.py" in f.lower()]
            if app_files:
                current_file = app_files[0] if os.path.isabs(app_files[0]) else os.path.join(project_path, app_files[0])
            else:
                current_file = os.path.join(project_path, "app.py")
        else:
            current_file = os.path.join(project_path, "main.py")
    
    # Final check: if message contains a filename that exists in project tree, use it
    for f_path in project_tree:
        fname = os.path.basename(f_path)
        fname_no_ext = os.path.splitext(fname)[0]
        # Check for full filename or name without extension (if it's long enough to be unique)
        if (fname.lower() in message.lower()) or (len(fname_no_ext) > 3 and fname_no_ext.lower() in message.lower()):
            if fname.endswith(".py") or fname.endswith(".js") or fname.endswith(".html") or fname.endswith(".css"):
                # Ensure we have an absolute path
                if not os.path.isabs(f_path) and project_path:
                    current_file = os.path.join(project_path, f_path)
                else:
                    current_file = f_path
                    
                # Update content if we switched files
                if os.path.exists(current_file):
                    try:
                        with open(current_file, 'r', encoding='utf-8') as f:
                            current_content = f.read()
                    except: pass
                break

    file_preview = current_content[:8000] if len(current_content) > 8000 else current_content
    filename = os.path.basename(current_file)

    hardware_info = context.get("hardware_info", {})
    hardware_desc = "CPU"
    if hardware_info.get("cuda_available"):
        hardware_desc = f"GPU (CUDA enabled: {hardware_info.get('details', 'NVIDIA GPU')})"
    elif hardware_info.get("has_nvidia"):
        hardware_desc = f"GPU (NVIDIA detected but CUDA check failed: {hardware_info.get('details', '')})"

    # --- PHASE 1: PLANNING ---
    if on_phase_update:
        on_phase_update("Planning", "🤔 **PHASE 1: PLANNING** - Architecting task graph...")

    # Cache check for intent parsing
    cache_key = f"{message}_{current_file}_{','.join(open_files)}"
    plan_data = None
    
    with _CACHE_LOCK:
        if cache_key in _INTENT_CACHE:
            plan_data = _INTENT_CACHE[cache_key]
            if on_phase_update:
                on_phase_update("Planning", "⚡ **PLANNING CACHE HIT** - Reusing existing task graph...")

    if not plan_data:
        # If it's an image analysis result, we want the planner to focus on the [TASK_SUMMARY]
        planning_message = message
        
        if "IMAGE_ANALYSIS_COMPLETE" in message:
            # Try to find a file name in the message if current_file is generic or main.py
            file_match = re.search(r'([a-zA-Z0-9_\-]+\.py)', message)
            if file_match:
                target_file_hint = file_match.group(1)
            elif "calculator" in message.lower():
                target_file_hint = "calculator.py"
            
            # ENSURE target_file_hint is NOT None
            if not target_file_hint:
                target_file_hint = current_file or os.path.join(project_path, "main.py")

            if "[TASK_SUMMARY]" in message:
                summary_match = re.search(r'\[TASK_SUMMARY\](.*?)\[/TASK_SUMMARY\]', message, re.DOTALL)
                if summary_match:
                    planning_message = f"Implement the following UI changes based on image analysis:\n{summary_match.group(1).strip()}\n\nIMPORTANT: Focus on {target_file_hint}. If this file does not exist, create it. If it exists, provide full code or a complete patch."

        # ABSOLUTE PATH FIX: Ensure target_file_hint is an absolute path for the planner
        if target_file_hint and not os.path.isabs(target_file_hint) and project_path:
            # Check if it exists in project tree first
            found_in_tree = False
            target_file_name = os.path.basename(target_file_hint)
            for p in project_tree:
                if p.endswith(target_file_name):
                    target_file_hint = p if os.path.isabs(p) else os.path.join(project_path, p)
                    found_in_tree = True
                    break
            if not found_in_tree:
                target_file_hint = os.path.join(project_path, target_file_hint)

        planner_prompt = f"""You are the PLANNER / Architect. Your role is to design a solution, not to write code.
    Analyze the user request and architect a comprehensive solution.
    
    Project Context:
    - Current File: {current_file}
    - Open Files: {open_files}
    - Hardware Environment: {hardware_desc}
    
    User Request: {planning_message}

    Current Code (from {filename}):
    {file_preview}

    INSTRUCTIONS:
    1. Deeply analyze the requirements. 
    2. Break down into 3-5 SPECIFIC, ACTIONABLE tasks (e.g., "Implement UI layout in tkinter", "Add calculation logic", "Link buttons to functions"). 
    3. Identify which files need to be created or modified. 
    4. ARCHITECTURE RULE: If you suggest splitting logic across multiple files (e.g., UI in main.py, logic in calculator.py), you MUST list ALL these files in the FILES section.
    5. Define CONSTRAINTS (language, framework, style) and SUCCESS CRITERIA.
    6. Output MUST follow this structured format exactly:
    
    <thought>[Detailed architectural analysis and file structure plan]</thought>
    PLAN: 1. Step 1 ...
    FILES: - list of files to be modified or created (BE EXPLICIT)
    CONSTRAINTS: - C1 ...
    SUCCESS_CRITERIA: - S1 ...
    TASKS: 
    - [ ] Specific Task 1
    - [ ] Specific Task 2
    - [ ] Specific Task 3
    
    IMPORTANT: Be explicit in the PLAN. Do NOT use generic task names like "Implement changes". Use specific descriptions like "Create calculator UI with tkinter" or "Implement addition logic".
    """
        
        planner_response = call_llm(planner_prompt, api_url, model, api_provider, token, stop_event=stop_event, system_prompt=SYSTEM_PROMPT, tier="small")
        
        def extract_section(text, header):
            # Normalize text to handle markdown bolding etc.
            clean_text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
            
            # Try finding with colon (e.g., PLAN:)
            pattern = rf'(?:^|\n){header}:\s*(.*?)(?:\n[A-Z_]{{3,}}:|$)'
            match = re.search(pattern, clean_text, re.DOTALL | re.IGNORECASE)
            if match and match.group(1).strip():
                return match.group(1).strip()
                
            # Try finding without colon (some LLMs might omit it)
            pattern = rf'(?:^|\n){header}\s*\n(.*?)(?:\n[A-Z_]{{3,}}:|$)'
            match = re.search(pattern, clean_text, re.DOTALL | re.IGNORECASE)
            if match and match.group(1).strip():
                return match.group(1).strip()
            return ""

        try:
            plan_text = extract_section(planner_response, "PLAN")
            files_text = extract_section(planner_response, "FILES")
            tasks_text = extract_section(planner_response, "TASKS")
            
            if tasks_text:
                tasks = []
                task_lines = tasks_text.split('\n')
                for i, line in enumerate(task_lines):
                    line = line.strip()
                    if not line: continue
                    # Remove checkbox or bullet
                    clean_task = re.sub(r'^[-*]\s*(\[[\sxX]\])?\s*', '', line).strip()
                    if clean_task:
                        tasks.append({"id": i+1, "task": clean_task, "file": target_file_hint, "type": "edit"})
                
                plan_data = {
                    "intent": "Modification",
                    "tasks": tasks,
                    "constraints": [extract_section(planner_response, "CONSTRAINTS")],
                    "success_criteria": [extract_section(planner_response, "SUCCESS_CRITERIA")]
                }
            else:
                # Fallback to JSON if it still exists
                json_match = re.search(r'\{.*\}', planner_response, re.DOTALL)
                if json_match:
                    plan_data = json.loads(json_match.group(0))
                else:
                    plan_data = {"tasks": [{"id": 1, "task": "Implement changes", "file": target_file_hint, "type": "edit"}]}
            
            if not plan_data.get("tasks"):
                plan_data["tasks"] = [{"id": 1, "task": "Implement changes", "file": target_file_hint, "type": "edit"}]

            with _CACHE_LOCK:
                _INTENT_CACHE[cache_key] = plan_data
        except Exception as e:
            logger.error(f"Planner parsing error: {e}")
            plan_data = {"tasks": [{"id": 1, "task": "Implement changes", "file": target_file_hint, "type": "edit"}]}

    # Final sanity check on plan_data tasks
    if not plan_data or not plan_data.get("tasks"):
        plan_data = {"tasks": [{"id": 1, "task": "Implement changes", "file": target_file_hint, "type": "edit"}]}

    tasks = []
    for t in plan_data.get("tasks", []):
        # ABSOLUTE PATH FIX: Ensure task files are absolute paths
        task_file = t.get("file")
        if not task_file:
            task_file = target_file_hint
            
        if task_file and not os.path.isabs(task_file) and project_path:
            # Check project tree for existing path
            found = False
            task_file_name = os.path.basename(task_file)
            for p in project_tree:
                if p.endswith(task_file_name):
                    task_file = p if os.path.isabs(p) else os.path.join(project_path, p)
                    found = True
                    break
            if not found:
                task_file = os.path.join(project_path, task_file)
        
        t["file"] = task_file # Update the plan data itself
        tasks.append({"name": t["task"], "status": "pending", "file": task_file})

    if on_tasks_update and tasks:
        on_tasks_update(tasks)

    if on_phase_update:
        on_phase_update("Planning", f"✅ **PLANNING COMPLETE**\n\n**Intent:** {plan_data.get('intent', 'Modification')}")

    # --- MAIN LOOP ---
    max_loops = 5 
    loop_count = 0
    start_time = time.time()
    current_tier = "small"
    failed_attempts = []
    applied_files = []
    resp_msg = ""
    
    while loop_count < max_loops:
        loop_count += 1
        applied_files = []
        
        # Group tasks by file for parallel execution
        tasks_to_run = plan_data.get("tasks", [])
        if not tasks_to_run:
            tasks_to_run = [{"id": 1, "task": "Implement changes", "file": target_file_hint, "type": "edit"}]
            
        file_to_tasks = {}
        for t in tasks_to_run:
            f = t.get("file")
            if not f:
                f = target_file_hint # Fallback to target hint
            
            if not os.path.isabs(f) and project_path:
                f = os.path.join(project_path, f)
            
            if f not in file_to_tasks:
                file_to_tasks[f] = []
            file_to_tasks[f].append(t)

        if on_phase_update:
            target_files = [os.path.basename(f) for f in file_to_tasks.keys()]
            on_phase_update("Coding", f"💻 **PHASE 2: EXECUTION** (Attempt {loop_count}/{max_loops}, Tier: {current_tier})\nFiles: {', '.join(target_files)}")

        def execute_task_group(file_path, task_list, tier, hardware_desc="CPU"):
            # Read current content of the file
            content = ""
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except:
                    pass
            
            is_image_request = "IMAGE_ANALYSIS_COMPLETE" in message
            
            executor_prompt = [
                {"role": "system", "content": f"""{SYSTEM_PROMPT}
Role: Executor Agent / Primary Coder
Task: Implement code changes for {os.path.basename(file_path)}.
Hardware Environment: {hardware_desc}

Instructions:
1. Provide the code changes for {file_path}.
2. Provide your solution ONLY in <patch> tags. Use the file attribute for clarity: <patch file="{file_path}">...</patch>.
3. You can EITHER provide a unified diff patch OR the FULL corrected code for the file (recommended for new files or major UI changes).
4. If "Current Content" is empty, you MUST provide the FULL code.
5. SELF-CONTAINED CODE: Every file you create must be fully functional.
6. No "To be implemented" or "Missing" sections. Provide the FULL working logic.
7. No explanations outside of <thought> tags.
"""},
                {"role": "user", "content": f"File: {file_path}\n\n[Current Content]\n```\n{content}\n```\n\n[Tasks to Perform]\n{json.dumps(task_list, indent=2)}\n\n[Context Request]\n{message}\n\n[Previous Failures]\n{json.dumps(failed_attempts[-2:], indent=2)}"}
            ]
            return call_llm(executor_prompt, api_url, model, api_provider, token, stop_event=stop_event, system_prompt=SYSTEM_PROMPT, tier=tier)

        # Run executors in parallel for different files
        current_patches = {}
        if not file_to_tasks:
            failed_attempts.append("Planner generated no file tasks.")
            current_tier = "large"
            continue

        with ThreadPoolExecutor(max_workers=max(1, min(len(file_to_tasks), 4))) as pool:
            future_to_file = {pool.submit(execute_task_group, f, ts, current_tier, hardware_desc): f for f, ts in file_to_tasks.items()}
            for future in future_to_file:
                path = future_to_file[future]
                try:
                    resp = future.result()
                    
                    # Parse patches from response
                    if resp:
                        logger.info(f"LLM Response length: {len(resp)}")
                        if 'error' in resp.lower():
                            logger.warning(f"LLM returned an error: {resp}")
                    else:
                        logger.warning(f"LLM returned empty response for {path}")
                        continue
                    
                    # Robust patch extraction (matches working IDE)
                    patch_pattern = r'<patch(?:\s+[^>]*?file=["\'](.*?)["\'][^>]*?)?\s*>(.*?)</patch>'
                    patch_matches = list(re.finditer(patch_pattern, resp, re.DOTALL))
                    found = False
                    for m in patch_matches:
                        p = m.group(1) or path
                        if not os.path.isabs(p) and project_path:
                            p = os.path.join(project_path, p)
                        current_patches[p] = m.group(2).strip()
                        found = True
                    
                    if not found:
                        # Fallback for full code in markdown blocks
                        code_matches = re.findall(r'```(?:python|xml|patch|diff)?\n(.*?)\n```', resp, re.DOTALL)
                        if code_matches:
                            # Use the largest code block if multiple exist
                            best_code = max(code_matches, key=len)
                            current_patches[path] = best_code.strip()
                            found = True
                        
                        # Fallback for raw code without tags if it's clearly code
                        if not found:
                            cleaned_resp = resp.strip()
                            if "import " in cleaned_resp or "def " in cleaned_resp or "class " in cleaned_resp:
                                current_patches[path] = cleaned_resp
                                found = True
                            elif "--- a/" in resp:
                                current_patches[path] = resp
                                found = True
                except Exception as e:
                    failed_attempts.append(f"Parallel executor error for {path}: {e}")

        if not current_patches:
            if on_phase_update:
                on_phase_update("Coding", f"⚠️ **WARNING** - No code changes generated for target files. (Loop {loop_count}/{max_loops})")
            current_tier = "large" # Scale up if no patches generated
            continue

        # --- PHASE 3: VALIDATION ---
        if on_phase_update:
            on_phase_update("Reviewing", f"🔍 **PHASE 3: VALIDATION** - Verifying {len(current_patches)} patches...")

        validation_results = []
        for path, patch in current_patches.items():
            if path.endswith(".py"):
                orig = ""
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        orig = f.read()
                
                res = apply_patch(path, orig, patch, dry_run=True)
                if res["success"]:
                    is_valid, err = verify_code_syntax(res["modified_content"], path)
                    if not is_valid:
                        validation_results.append(f"Syntax error in {path}: {err}")
                else:
                    validation_results.append(f"Patch failed for {path}: {res['error']}")

        if validation_results:
            if on_phase_update:
                on_phase_update("Reviewing", f"❌ **VALIDATION FAILED** - Found {len(validation_results)} issues. Retrying...")
            failed_attempts.append({"attempt": loop_count, "errors": validation_results})
            current_tier = "large" # Scale up on validation failure
            
            # If validation fails twice, we might need to re-plan (handled by loop count/tier logic)
            if len(failed_attempts) >= 2:
                if on_phase_update:
                    on_phase_update("Planning", "🔄 **RE-PLANNING** - Multiple failures detected, adjusting strategy...")
                # Clear cache and loop count to force fresh start if we were to continue, 
                # but here we just let the loop continue with "large" tier.
            continue 

        # --- PHASE 4: APPLICATION ---
        if on_phase_update:
            on_phase_update("Applying", "🚀 **PHASE 4: APPLICATION** - Applying patches...")

        last_modified_content = current_content
        applied_files_full = []
        for path, patch in current_patches.items():
            orig = ""
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    orig = f.read()
            else:
                os.makedirs(os.path.dirname(path), exist_ok=True)
            
            res = apply_patch(path, orig, patch, backup_mgr=backup_mgr)
            if res["success"]:
                applied_files_full.append(path)
                applied_files.append(os.path.basename(path))
                if path == current_file:
                    last_modified_content = res["modified_content"]

        if on_phase_update:
            on_phase_update("Done", f"✅ **SUCCESS** - Applied changes to {len(applied_files)} files.")

        if on_tasks_update and tasks:
            for t in tasks: t["status"] = "completed"
            on_tasks_update(tasks)

        if applied_files_full:
            # Final Verification: Ensure the files were actually modified
            real_applied = []
            for f_path in applied_files_full:
                if os.path.exists(f_path):
                    real_applied.append(f_path)
            
            if real_applied:
                # Check if the user wants to continue thinking/improving
                resp_msg = f"✅ **SUCCESS** - Applied changes to {len(real_applied)} files:\n" + "\n".join([f"- {os.path.basename(f)}" for f in real_applied])
                resp_msg += "\n\nI've implemented the core calculator features and UI based on your image. Would you like me to refine the colors further or add more scientific functions?"
                break
            else:
                resp_msg = "❌ **ERROR** - Agents claimed to apply changes, but no files were modified. Retrying with higher tier..."
                # Let it loop if count < max
                if loop_count < max_loops:
                    current_tier = "large"
                    continue
    else:
        resp_msg = "❌ **FAILURE** - Could not generate or apply valid changes after 5 attempts. Please check the logs or try rephrasing your request."

    return {
        "response": resp_msg,
        "actions_performed": [{"type": "modify_file", "file": f} for f in applied_files],
        "requires_approval": False
    }

def handle_command_request(message, context, api_url, model, api_provider, token, execute_actions=True, stop_event=None):
    """Handle requests to run terminal commands"""
    from core.llm import call_llm
    project_path = context.get("project_path")
    prompt = f"Suggest shell command for: {message}. Project path: {project_path}. Respond ONLY with command string."
    response = call_llm(prompt, api_url, model, api_provider, token, stop_event=stop_event).strip()
    if "```" in response:
        response = re.search(r'```(?:\w+)?\n(.*?)\n```', response, re.DOTALL).group(1).strip()
    return {
        "response": f"🚀 Executing: `{response}`",
        "actions_performed": [{"type": "run_command", "command": response, "cwd": project_path}],
        "requires_approval": True
    }

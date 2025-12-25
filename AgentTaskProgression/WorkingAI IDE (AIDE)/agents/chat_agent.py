"""
Chat Agent - Enhanced with a Multi-Agent pipeline (Planning, Coding, Reviewing, Testing, Done)
"""
import os
import re
import difflib
import subprocess
import json

def chat_agent(message, api_url, model, api_provider="openai", token=None, context=None, execute_actions=True, conversation_history=None, on_tasks_update=None, on_phase_update=None, stop_event=None):
    """Enhanced chat agent with multi-agent pipeline"""
    from core.llm import call_llm
    
    # Check for cancellation
    if stop_event and stop_event.is_set():
        return {"response": "Task cancelled by user.", "status": "cancelled"}
    
    # Detect if this is a file modification request
    modification_keywords = ["modify", "change", "update", "edit", "fix", "add", "remove", "make", "set"]
    is_modification = any(keyword in message.lower() for keyword in modification_keywords)
    
    # Detect command execution requests
    command_keywords = ["run", "execute", "terminal", "shell", "command", "pip", "python", "npm", "git"]
    is_command = any(keyword in message.lower() for keyword in command_keywords)
    
    if is_modification and context:
        # This is a modification request - use multi-agent approach
        return handle_modification_request(message, context, api_url, model, api_provider, token, execute_actions, on_tasks_update, on_phase_update, stop_event=stop_event)
    elif is_command and not is_modification:
        # Command execution request
        return handle_command_request(message, context, api_url, model, api_provider, token, execute_actions, stop_event=stop_event)
    else:
        # General chat
        prompt = f"""User: {message}

{f"Conversation History: {conversation_history}" if conversation_history else ""}

Context: {context if context else 'No context provided'}

You are an AI coding assistant. Provide helpful responses about coding, debugging, or project planning.
If the user asks to modify code, provide ONLY a unified diff patch (not full code).
If they ask for explanations, provide clear explanations.
If they ask for project planning, help them break down the project.

IMPORTANT: For code modifications, respond ONLY with a unified diff patch format:
--- a/filename.py
+++ b/filename.py
@@ -line,count +line,count @@
-old line
+new line

Do NOT include explanations or markdown. Just the patch."""
        
        response = call_llm(prompt, api_url, model, api_provider, token, stop_event=stop_event)
        
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
    
    # Use current file if available, otherwise check open files, then default to main.py
    if current_file and os.path.exists(current_file):
        try:
            with open(current_file, 'r', encoding='utf-8') as f:
                current_content = f.read()
        except Exception as e:
            return {"response": f"Error reading file: {e}", "actions_performed": [], "requires_approval": False}
    elif open_files and os.path.exists(open_files[0]):
        current_file = open_files[0]
        try:
            with open(current_file, 'r', encoding='utf-8') as f:
                current_content = f.read()
        except:
            current_content = ""
    else:
        current_content = ""
        # Look for keywords in message to guess the file
        if "calculator" in message.lower():
            current_file = os.path.join(project_path, "calculator.py")
        elif "app" in message.lower():
            current_file = os.path.join(project_path, "app.py")
        else:
            current_file = os.path.join(project_path, "main.py")
    
    file_preview = current_content[:8000] if len(current_content) > 8000 else current_content
    filename = os.path.basename(current_file)

    # --- PHASE 1: PLANNING ---
    if on_phase_update:
        on_phase_update("Planning", "🤔 **PHASE 1: PLANNING** - Architecting solution...")

    hardware_info = context.get("hardware_info", {})
    hardware_desc = "CPU"
    if hardware_info.get("cuda_available"):
        hardware_desc = f"GPU (CUDA enabled: {hardware_info.get('details', 'NVIDIA GPU')})"
    elif hardware_info.get("has_nvidia"):
        hardware_desc = f"GPU (NVIDIA detected but CUDA check failed: {hardware_info.get('details', '')})"

    planner_prompt = f"""You are the PLANNER / Architect. Your role is to design a solution, not to write code.
    Analyze the user request and architect a comprehensive solution.
    
    Project Context:
    - Current File: {current_file}
    - Open Files: {open_files}
    - Hardware Environment: {hardware_desc}
    
    User Request: {message}

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
    
    planner_response = call_llm(planner_prompt, api_url, model, api_provider, token, stop_event=stop_event)
    
    # Check for cancellation after planning
    if stop_event and stop_event.is_set():
        return {"response": "Task cancelled after planning.", "status": "cancelled"}
    
    def extract_section(text, header):
        # Improved extraction that handles different formatting and ensures we get the content
        # Normalize text to handle markdown bolding etc.
        clean_text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        
        # Try finding with markdown headers first (e.g., ### PLAN)
        pattern = rf'(?:^|\n)#+\s*{header}\s*\n(.*?)(?:\n#+|\n[A-Z_]{{3,}}:|$)'
        match = re.search(pattern, clean_text, re.DOTALL | re.IGNORECASE)
        if match and match.group(1).strip():
            return match.group(1).strip()
            
        # Try finding with colon (e.g., PLAN:)
        pattern = rf'(?:^|\n){header}:\s*(.*?)(?:\n#+|\n[A-Z_]{{3,}}:|$)'
        match = re.search(pattern, clean_text, re.DOTALL | re.IGNORECASE)
        if match and match.group(1).strip():
            return match.group(1).strip()
            
        # Try finding without colon (some LLMs might omit it)
        pattern = rf'(?:^|\n){header}\s*\n(.*?)(?:\n#+|\n[A-Z_]{{3,}}:|$)'
        match = re.search(pattern, clean_text, re.DOTALL | re.IGNORECASE)
        if match and match.group(1).strip():
            return match.group(1).strip()
            
        # Fallback: line-by-line search
        lines = text.split('\n')
        start_idx = -1
        for i, line in enumerate(lines):
            clean_line = re.sub(r'[*_#]', '', line).strip().upper()
            if clean_line == header.upper() or clean_line.startswith(header.upper() + ":"):
                start_idx = i
                break
        
        if start_idx != -1:
            content = []
            for line in lines[start_idx+1:]:
                # If we hit another header-like line, stop
                u_line = line.strip().upper()
                if re.match(r'^#+\s*[A-Z_]{3,}', u_line) or re.match(r'^[A-Z_]{3,}:', u_line):
                    break
                content.append(line)
            return "\n".join(content).strip()
        return ""

    planner_plan = extract_section(planner_response, "PLAN")
    planner_files = extract_section(planner_response, "FILES")
    planner_constraints = extract_section(planner_response, "CONSTRAINTS")
    planner_criteria = extract_section(planner_response, "SUCCESS_CRITERIA")
    
    def check_decision(text, positive_keywords, negative_keywords):
        """Robustly check for a decision in agent response"""
        # Look for [DECISION] format first
        decision_match = re.search(r'DECISION:\s*\[?(\w+)\]?', text, re.IGNORECASE)
        if decision_match:
            val = decision_match.group(1).upper()
            if any(k.upper() in val for k in positive_keywords):
                return True
            if any(k.upper() in val for k in negative_keywords):
                return False
        
        # Fallback: check for keywords in the whole text (looking for emojis or bold)
        text_upper = text.upper()
        # Check positive keywords (e.g., APPROVED, PASS, MERGE)
        for k in positive_keywords:
            if f"[{k.upper()}]" in text_upper or f"**{k.upper()}**" in text_upper or f"✅ {k.upper()}" in text_upper:
                return True
        
        # Check negative keywords (e.g., REJECT, FAIL)
        for k in negative_keywords:
            if f"[{k.upper()}]" in text_upper or f"**{k.upper()}**" in text_upper or f"❌ {k.upper()}" in text_upper:
                return False
                
        # Final fallback: just look for the words
        for k in positive_keywords:
            if k.upper() in text_upper: return True
        return False

    tasks = []
    # More robust extraction for TASKS
    tasks_text = extract_section(planner_response, "TASKS")
    if tasks_text:
        # Try to parse line by line (e.g., "- [ ] Task 1")
        for line in tasks_text.split('\n'):
            line = line.strip()
            # Handle both "- [ ] Task" and "- Task" formats
            if line.startswith('-'):
                name = re.sub(r'^- \[[ xX]?\]\s*', '', line)
                name = re.sub(r'^- \s*', '', name).strip()
                # Filter out generic tasks if we already have specific ones
                generic_names = ["implement changes", "analyze requirements", "verify solution", "fix issues"]
                if name and not any(g == name.lower() for g in generic_names):
                    tasks.append({"name": name, "status": "pending"})
                elif name and not tasks: # Allow generic only if nothing else found yet
                     tasks.append({"name": name, "status": "pending"})
    
    # Fallback tasks only if absolutely none found
    if not tasks:
        tasks = [{"name": "Analyze requirements", "status": "pending"},
                 {"name": "Implement core logic", "status": "pending"},
                 {"name": "Verify success criteria", "status": "pending"}]

    if on_tasks_update and tasks:
        on_tasks_update(tasks)
    
    # Ensure plan is visible even if extraction was slightly off
    if not planner_plan or len(planner_plan) < 5:
        planner_plan = f"1. Analyze requirements for {filename}\n2. Implement the core logic using appropriate libraries\n3. Verify the implementation against user request: {message}"
    
    display_plan = planner_plan
    
    if on_phase_update:
        display_msg = f"✅ **PLANNING COMPLETE**\n\n**Plan:**\n{display_plan}"
        if planner_files:
            display_msg += f"\n\n**Files:**\n{planner_files}"
        on_phase_update("Planning", display_msg)

    # Initial task status
    if tasks:
        tasks[0]["status"] = "in_progress"
        if on_tasks_update: on_tasks_update(tasks)

    # --- MAIN LOOP ---
    max_loops = 10
    loop_count = 0
    accumulated_patches = {} # Map of filepath -> patch_text (Persists across loops)
    last_feedback = ""
    
    coder_history = [
        {"role": "system", "content": f"""You are the PRIMARY CODER. Your role is to implement the PLAN.
        Hardware Environment: {hardware_desc}
        
        RULES:
        1. Implement ALL files mentioned in the PLAN. 
        2. PERSISTENCE: If you previously provided some files but the plan is not yet complete, you must provide the remaining files.
        3. ACCUMULATION: The system remembers the files you've already implemented. Focus on completing the missing parts mentioned in the feedback.
        4. SELF-CONTAINED CODE: Every file you create must be fully functional. If you import a class like 'Calculator' from 'calculator', you MUST provide the 'calculator.py' file with that class definition in a <patch> tag.
        5. No "To be implemented" or "Missing" sections. Provide the FULL working logic.
        6. If you need to see other files, use <search>query</search>.
        7. Provide your solution ONLY in <patch> tags. Use the file attribute for clarity: <patch file="path/to/file.py">...</patch>.
        8. Each <patch> MUST include the file path in its header (--- a/path/to/file) OR in the tag attribute (file="...").
        9. If creating a new file, provide the FULL CONTENT in <patch> tags.
        10. DO NOT provide explanations outside of <thought> tags.
        11. All code must be compilation-safe. If the Reviewer/Tester rejects it, fix it immediately.
        12. Ensure all imports in your code correspond to either existing files or files you are creating in this response.
        13. PRIORITIZE ACTIVE FILE: The Primary File provided is the one the user is currently looking at. Focus your main changes there.
        """},
        {"role": "user", "content": f"""
         PLAN: {planner_plan}
         FILES TO CREATE/MODIFY: {planner_files}
         CONSTRAINTS: {planner_constraints}
         SUCCESS CRITERIA: {planner_criteria}
         """},
        {"role": "user", "content": f"User Request: {message}\n\nPrimary File: {current_file}\nContent:\n{file_preview if file_preview else '[Empty File]'}"}
    ]

    while loop_count < max_loops:
        loop_count += 1
        
        # Build progress summary for the coder
        if accumulated_patches:
            progress_msg = "Current Progress (Files already implemented):\n"
            for f in accumulated_patches.keys():
                rel_f = os.path.relpath(f, project_path) if project_path and f.startswith(project_path) else f
                progress_msg += f"- {rel_f}\n"
            progress_msg += "\nPlease implement the remaining files or fix the issues mentioned below."
            coder_history.append({"role": "user", "content": progress_msg})

        # Update task status if we're retrying
        if loop_count > 1 and tasks:
            for t in tasks:
                if t["status"] == "in_progress":
                    t["status"] = "pending"
            tasks[min(loop_count - 1, len(tasks)-1)]["status"] = "in_progress"
            if on_tasks_update: on_tasks_update(list(tasks))

        # --- PHASE 2: CODING ---
        if on_phase_update:
            on_phase_update("Coding", f"💻 **PHASE 2: CODING** (Attempt {loop_count}/{max_loops})")

        coder_iterations = 0
        max_coder_iterations = 5
        current_patches = {} # Map of filepath -> patch_text (Current iteration only)
        last_search = ""
        
        while coder_iterations < max_coder_iterations:
            coder_iterations += 1
            
            # Update task status
            active_task = None
            for t in tasks:
                if t.get("status") == "pending":
                    t["status"] = "in_progress"
                    active_task = t["name"]
                    if on_tasks_update: on_tasks_update(list(tasks))
                    break
                elif t.get("status") == "in_progress":
                    active_task = t["name"]
                    break
            
            if on_phase_update:
                status_msg = f"🔄 **Iteration {coder_iterations}/{max_coder_iterations}**\nThinking..."
                if active_task: status_msg += f"\nWorking on: {active_task}"
                on_phase_update("Coding", status_msg)

            coder_response = call_llm(coder_history, api_url, model, api_provider, token, stop_event=stop_event)
            if not coder_response or coder_response.startswith("Error"): 
                if on_phase_update: on_phase_update("Coding", "❌ **LLM Call Failed**")
                break
            
            # Extract thought for transparency
            thought_match = re.search(r'<thought>(.*?)</thought>', coder_response, re.DOTALL)
            iteration_thought = thought_match.group(1).strip() if thought_match else "Implementing requested changes..."
            
            if on_phase_update:
                status_msg = f"🔄 **Iteration {coder_iterations}/{max_coder_iterations}**\n\n**Purpose:** {iteration_thought}"
                if active_task: status_msg += f"\n\n**Current Task:** {active_task}"
                on_phase_update("Coding", status_msg)

            coder_history.append({"role": "assistant", "content": coder_response})
            
            # Check for search action
            search_match = re.search(r'<search>(.*?)</search>', coder_response, re.DOTALL)
            if search_match:
                query = search_match.group(1).strip()
                if query == last_search:
                    coder_history.append({"role": "user", "content": "You already searched for that. Please provide a different query or a <patch>."})
                    continue
                last_search = query
                if on_phase_update: on_phase_update("Coding", f"🔍 **Searching codebase for:** `{query}`")
                search_results = perform_agent_search(query, project_path)
                
                # Enhanced feedback if file not found
                if "No matches found" in search_results and (query.endswith('.py') or query.endswith('.js')):
                    search_results += f"\nNote: The file '{query}' does not exist yet. You should create it if it's needed for the plan."
                
                coder_history.append({"role": "user", "content": f"Search Results:\n{search_results}"})
                continue
                
            # Check for patches (support multiple)
            # Find all <patch> tags and their attributes
            # More robust regex: handles extra attributes, different spacing, and both ' and "
            patch_pattern = r'<patch(?:\s+[^>]*?file=["\'](.*?)["\'][^>]*?)?\s*>(.*?)</patch>'
            found_patches_with_attr = re.findall(patch_pattern, coder_response, re.DOTALL)
            
            if not found_patches_with_attr:
                # Fallback: Look for code blocks if no <patch> tags
                # Accept more variations of code blocks and try to be more lenient with content
                code_blocks = re.findall(r'```(?:\w+)?\n(.*?)\n```', coder_response, re.DOTALL)
                for block in code_blocks:
                    content = block.strip()
                    # If it looks like a patch or significant code, accept it
                    if "--- a/" in content or "@@" in content or content.startswith(("import ", "from ", "def ", "class ", "print(")):
                        found_patches_with_attr.append(("", content))
            
            if found_patches_with_attr:
                for attr_file, patch_text in found_patches_with_attr:
                    # Identify target file
                    target_file = None
                    
                    # 1. Check tag attribute first
                    if attr_file:
                        target_file = os.path.join(project_path, attr_file.strip())
                    
                    # 2. Check patch header if no attribute or as double check
                    if not target_file or not os.path.exists(target_file):
                        header_match = re.search(r'--- a/(.*)', patch_text)
                        if header_match:
                            target_file_rel = header_match.group(1).strip()
                            target_file = os.path.join(project_path, target_file_rel)
                    
                    # 3. Fallback to current_file if still not found
                    if not target_file:
                        target_file = current_file
                    
                    # Store patch
                    current_patches[target_file] = patch_text
                    # Also update accumulated_patches
                    accumulated_patches[target_file] = patch_text
                
                if on_phase_update: on_phase_update("Coding", f"✅ **Patches generated for {len(current_patches)} file(s).**")
                break # Exit iteration loop if patches found
            else:
                # If no patches found and not searching, provide feedback to coder
                if not search_match:
                    feedback = "I couldn't find any <patch> tags or valid code blocks in your response. Please provide your implementation wrapped in <patch file=\"...\">...</patch> tags."
                    coder_history.append({"role": "user", "content": feedback})
                    if on_phase_update: on_phase_update("Coding", "⚠️ **No patch detected. Retrying with feedback...**")
                
        if not current_patches and not accumulated_patches:
            if on_phase_update: on_phase_update("Coding", "❌ **Coding failed to produce a valid patch.**")
            continue

        # --- PHASE 3: REVIEWING ---
        if on_phase_update:
            on_phase_update("Reviewing", "🔍 **PHASE 3: REVIEWING** - Static analysis...")
        
        # Build review context from ALL accumulated patches
        review_context = "Proposed Changes (Cumulative):\n"
        for f, p in accumulated_patches.items():
            review_context += f"\nFile: {os.path.relpath(f, project_path) if project_path and f.startswith(project_path) else f}\nPatch:\n{p}\n"

        reviewer_prompt = f"""You are the REVIEWER. Analyze the proposed patches for logic errors, missing imports, or edge cases.
        
        Context:
        - Plan: {planner_plan}
        - Constraints: {planner_constraints}
        {review_context}
        
        RULES:
        1. If there are CRITICAL issues (bugs, missing files, broken logic), respond with DECISION: [REJECT].
        2. CROSS-FILE CHECK: If a patch imports a module (e.g., 'import calculator'), verify if that module is either already in the codebase or provided in the current patches. If not, it's a [BLOCKING] issue.
        3. List issues as [BLOCKING] or [NON-BLOCKING].
        4. If it looks good, respond with DECISION: [APPROVED].
        5. Be concise.
        """
        
        reviewer_response = call_llm(reviewer_prompt, api_url, model, api_provider, token, stop_event=stop_event)
        is_approved = check_decision(reviewer_response, ["APPROVED", "PASS"], ["REJECT", "FAIL"])
        
        if on_phase_update:
            status = "✅ **APPROVED**" if is_approved else "❌ **REJECTED**"
            on_phase_update("Reviewing", f"🔍 **PHASE 3: REVIEWING**\n\n**Reviewer Decision:** {status}\n\n{reviewer_response}")

        if not is_approved:
            last_feedback = reviewer_response
            coder_history.append({"role": "user", "content": f"Reviewer rejected your changes:\n{reviewer_response}\nPlease fix these issues."})
            continue

        # --- PHASE 4: TESTING ---
        if on_phase_update:
            on_phase_update("Testing", "🧪 **PHASE 4: TESTING** - Simulating execution...")
            
        tester_prompt = f"""You are the TESTER. Mentally simulate the execution of the proposed changes.
        
        Proposed Changes:
        {review_context}
        
        SUCCESS CRITERIA:
        {planner_criteria}
        
        RULES:
        1. If it will likely fail at runtime or miss success criteria, respond with DECISION: [FAIL].
        2. MODULARITY & COMPLETENESS CHECK: Ensure all imported classes or functions (e.g., 'Calculator' from 'calculator') are actually defined in the files provided or existing ones. 
        3. NO PLACEHOLDERS: If you see comments like "# To be implemented" or missing logic in critical methods (like button clicks or calculation evaluation), respond with DECISION: [FAIL].
        4. Describe failure scenarios clearly.
        5. If it passes simulation, respond with DECISION: [PASS].
        """
        
        tester_response = call_llm(tester_prompt, api_url, model, api_provider, token, stop_event=stop_event)
        test_passed = check_decision(tester_response, ["PASS", "APPROVED"], ["FAIL", "REJECT"])
        
        if on_phase_update:
            status = "✅ **PASS**" if test_passed else "❌ **FAIL**"
            on_phase_update("Testing", f"🧪 **PHASE 4: TESTING**\n\n**Tester Decision:** {status}\n\n{tester_response}")

        if not test_passed:
            last_feedback = tester_response
            coder_history.append({"role": "user", "content": f"Tester found potential issues:\n{tester_response}\nPlease fix these."})
            continue

        # --- PHASE 5: INTEGRATION ---
        if on_phase_update:
            on_phase_update("Integration", "🏗️ **PHASE 5: INTEGRATION** - Final verification...")
            
        integrator_prompt = f"""You are the INTEGRATOR. Verify if the plan has been fully satisfied.
        
        PLAN: {planner_plan}
        CHANGES: {review_context}
        
        DECISION: [MERGE] if complete, [REJECT] if something is missing.
        """
        
        integrator_response = call_llm(integrator_prompt, api_url, model, api_provider, token, stop_event=stop_event)
        should_merge = check_decision(integrator_response, ["MERGE", "APPROVE", "PASS"], ["REJECT", "FAIL"])
        
        if on_phase_update:
            status = "✅ **MERGE**" if should_merge else "❌ **REJECT**"
            on_phase_update("Integration", f"🏗️ **PHASE 5: INTEGRATION**\n\n**Integrator Decision:** {status}\n\n{integrator_response}")

        if should_merge:
            final_patches = accumulated_patches
            break
        else:
            last_feedback = integrator_response
            coder_history.append({"role": "user", "content": f"Integrator rejected the merge:\n{integrator_response}\nPlease complete the implementation."})


    if final_patches:
        # Final task update
        if on_tasks_update and tasks:
            for t in tasks:
                t["status"] = "completed"
            on_tasks_update(list(tasks))

        # --- PHASE 6: DONE ---
        if on_phase_update: on_phase_update("Done", "🏁 **PHASE 6: DONE** - Summarizing results...")
        
        # Build summary context
        summary_context = f"Files modified/created:\n"
        for f in final_patches.keys():
            rel_path = os.path.relpath(f, project_path) if project_path and f.startswith(project_path) else f
            summary_context += f"- {rel_path}\n"

        summary_prompt = f"""Summarize the changes made for the user.
        Request: {message}
        Changes:
        {summary_context}
        
        Keep it concise and friendly. Focus on what was achieved."""
        
        summary = call_llm(summary_prompt, api_url, model, api_provider, token, stop_event=stop_event)
        
        if on_phase_update: 
            on_phase_update("Done", f"✅ **SUCCESS**\n\n{summary}")
            
        actions = []
        last_modified_content = current_content
        
        for filepath, patch_text in final_patches.items():
            # Read current content of this specific file if it exists
            file_content = ""
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                except:
                    pass
            
            if execute_actions:
                apply_result = apply_patch(filepath, file_content, patch_text, backup_mgr=backup_mgr)
                if apply_result["success"]:
                    content = apply_result["modified_content"]
                    if filepath == current_file:
                        last_modified_content = content
            else:
                apply_result = apply_patch(filepath, file_content, patch_text, dry_run=True)
                if apply_result["success"]:
                    content = apply_result["modified_content"]
                    if filepath == current_file:
                        last_modified_content = content
            
            actions.append({
                "type": "modify_file",
                "file": filepath,
                "patch": patch_text,
                "content": content if 'content' in locals() else None
            })

        return {
              "response": summary,
              "actions_performed": actions,
              "requires_approval": not execute_actions,
              "modified_content": last_modified_content
          }
    else:
        # Pipeline failed
        error_msg = "The multi-agent pipeline failed to reach a consensus on a valid solution."
        if last_feedback:
            error_msg += f"\n\n**Last Agent Feedback:**\n{last_feedback}"
            
        if on_phase_update: on_phase_update("Done", f"❌ **Pipeline failed after {max_loops} attempts.**\n\n{error_msg}")
        return {
            "response": error_msg,
            "actions_performed": [],
            "requires_approval": False
        }

def handle_command_request(message, context, api_url, model, api_provider, token, execute_actions=True):
    """Handle requests to run terminal commands"""
    from core.llm import call_llm
    project_path = context.get("project_path")
    prompt = f"Suggest shell command for: {message}. Project path: {project_path}. Respond ONLY with command string."
    response = call_llm(prompt, api_url, model, api_provider, token).strip()
    if "```" in response:
        response = re.search(r'```(?:\w+)?\n(.*?)\n```', response, re.DOTALL).group(1).strip()
    return {
        "response": f"🚀 Executing: `{response}`",
        "actions_performed": [{"type": "run_command", "command": response, "cwd": project_path}],
        "requires_approval": True
    }

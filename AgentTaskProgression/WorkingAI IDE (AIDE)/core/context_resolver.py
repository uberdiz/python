import os
import re

class ContextResolver:
    """
    Resolves context tokens in prompts (e.g., @Agent, #file.py).
    Ensures prompts are enhanced with actual content before processing.
    """
    def __init__(self, app):
        self.app = app
        
    def resolve(self, message):
        """
        Parse message for context tokens and expand them.
        Returns: (resolved_message, attachments_list)
        """
        attachments = []
        resolved_message = message
        
        # 1. Resolve File References (#filename)
        # Regex to find #filename.ext or #filename
        # We need to be careful not to match random hashtags, so we look for files that actually exist
        # or match the pattern #[\w.-]+
        
        # Strategy: Find all candidates, check if they exist in open files or project
        potential_files = re.findall(r'#([\w\-.\\/]+)', message)
        
        for fname in potential_files:
            content = self._fetch_file_content(fname)
            if content:
                # Replace the tag with a marker or keep it and append content?
                # Usually better to append content in a structured way
                attachments.append(f"File: {fname}\n```\n{content}\n```")
                
        # 2. Resolve Agent Mentions (@Agent)
        # This is mostly for routing, but we can verify they exist
        # logic handled by caller mostly, but we can validate here
        
        # 3. Resolve Terminal Output (@Terminal or similar?)
        # If user asks for "last error", we might fetch it
        if "@terminal" in message.lower() or "terminal output" in message.lower():
            term_output = self._get_terminal_output()
            if term_output:
                attachments.append(f"Terminal Output:\n```\n{term_output}\n```")
        
        # Combine
        if attachments:
            resolved_message += "\n\n--- Context ---\n" + "\n\n".join(attachments)
            
        return resolved_message

    def _fetch_file_content(self, filename):
        """Find file and return content"""
        # Try exact path
        if os.path.exists(filename):
            return self._read_file(filename)
            
        # Try in project root
        if self.app.project_path:
            p = os.path.join(self.app.project_path, filename)
            if os.path.exists(p):
                return self._read_file(p)
                
        # Try in open tabs
        if hasattr(self.app, 'editor_tabs'):
            for path in self.app.editor_tabs.get_open_files():
                if os.path.basename(path) == filename:
                    return self._read_file(path)
                    
        return None

    def _read_file(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except:
            return None

    def _get_terminal_output(self):
        # This is tricky as we need access to the terminal widget
        # The app structure puts terminal in layout_manager -> bottom_panel -> output_panels
        try:
            # Assuming typical path (this is fragile but best effort)
            term = self.app.layout_manager.bottom_panel.output_panels.terminal
            return term.get_output()
        except:
            return None

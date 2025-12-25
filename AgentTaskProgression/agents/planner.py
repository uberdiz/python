"""
Planner Agent function for compatibility
"""

def planner_agent(prompt, api_url, model, api_provider="openai", token=None):
    """Standalone planner agent function for compatibility"""
    from core.llm import call_llm
    
    system_prompt = f"""Create a project plan for: {prompt}

    Provide a JSON response with:
    - project_name: Name of the project
    - description: Brief description
    - files: List of files to create
    - dependencies: List of Python packages needed
    - steps: Implementation steps
    - features: Key features
    
    Keep it realistic and achievable."""
    
    response = call_llm(system_prompt, api_url, model, api_provider, token)
    
    # Try to parse JSON response
    try:
        import json
        start = response.find('{')
        end = response.rfind('}') + 1
        if start >= 0 and end > start:
            json_str = response[start:end]
            return json.loads(json_str)
    except:
        pass
    
    # Fallback plan
    return {
        "project_name": f"AI Project: {prompt[:30]}...",
        "description": f"Project generated from: {prompt}",
        "files": ["main.py", "utils.py", "README.md", "requirements.txt"],
        "dependencies": [],
        "steps": ["Initialize project", "Create basic structure", "Implement core features"],
        "features": ["AI-generated code", "Modular design", "Easy to extend"]
    }
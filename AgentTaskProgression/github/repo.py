"""
GitHub Repository Operations - FIXED VERSION
"""
import os
import requests
import json

def create_github_repo(token, repo_name, description="", private=False):
    """Create a new GitHub repository"""
    try:
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
        
        data = {
            "name": repo_name,
            "description": description,
            "private": private,
            "auto_init": False  # Don't create README automatically
        }
        
        response = requests.post(
            "https://api.github.com/user/repos",
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 201:
            repo_data = response.json()
            return {
                "success": True,
                "clone_url": repo_data.get("clone_url"),
                "html_url": repo_data.get("html_url"),
                "full_name": repo_data.get("full_name")
            }
        else:
            error_msg = response.json().get("message", f"Status: {response.status_code}")
            return {
                "success": False,
                "error": error_msg
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def get_user_repos(token):
    """Get user's repositories"""
    try:
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        response = requests.get(
            "https://api.github.com/user/repos",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            repos = response.json()
            return [{
                "name": repo.get("name", ""),
                "full_name": repo.get("full_name", ""),
                "description": repo.get("description", ""),
                "url": repo.get("html_url", ""),
                "private": repo.get("private", False)
            } for repo in repos]
        return []
    except Exception as e:
        print(f"Error getting repos: {e}")
        return []

def delete_github_repo(token, repo_name):
    """Delete a GitHub repository"""
    try:
        # Get username from token
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # First get user info
        user_response = requests.get("https://api.github.com/user", headers=headers)
        if user_response.status_code == 200:
            username = user_response.json().get("login")
            
            # Delete repo
            delete_url = f"https://api.github.com/repos/{username}/{repo_name}"
            delete_response = requests.delete(delete_url, headers=headers)
            
            return delete_response.status_code == 204
    except Exception as e:
        print(f"Error deleting repo: {e}")
        return False
    
    return False
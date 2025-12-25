"""
Dependency Management
"""
import subprocess
import sys
try:
    import importlib.metadata as _imd
except Exception:
    _imd = None
import os

def check_dependency(package_name):
    """Check if package is installed"""
    try:
        if _imd:
            try:
                _imd.version(package_name)
                return True
            except Exception:
                pass
        out = subprocess.run([sys.executable, "-m", "pip", "show", package_name], capture_output=True, text=True)
        return out.returncode == 0 and package_name.lower() in out.stdout.lower()
    except Exception:
        return False

def install_dependency(package_name):
    """Install a package"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        return True
    except:
        return False

def get_installed_packages():
    """Get list of installed packages"""
    installed = []
    try:
        if _imd:
            for dist in _imd.distributions():
                try:
                    installed.append(dist.metadata.get("Name", "").lower())
                except Exception:
                    pass
        else:
            out = subprocess.run([sys.executable, "-m", "pip", "list"], capture_output=True, text=True)
            for line in out.stdout.splitlines()[2:]:
                parts = line.split()
                if parts:
                    installed.append(parts[0].lower())
    except Exception:
        pass
    return installed

def check_project_dependencies(project_path):
    """Check project dependencies from requirements.txt"""
    req_file = os.path.join(project_path, "requirements.txt")
    missing = []
    
    if os.path.exists(req_file):
        with open(req_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    # Parse package name (remove version specifiers)
                    package_name = line.split('==')[0].split('>=')[0].split('<=')[0].strip()
                    if not check_dependency(package_name):
                        missing.append(package_name)
    
    return missing

def generate_requirements(project_path, packages):
    """Generate requirements.txt file"""
    req_file = os.path.join(project_path, "requirements.txt")
    with open(req_file, 'w') as f:
        for package in packages:
            f.write(f"{package}\n")

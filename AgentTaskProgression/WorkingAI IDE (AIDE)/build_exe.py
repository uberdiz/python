import PyInstaller.__main__
import os
import sys
import shutil

def build():
    # Define the main entry point
    entry_point = "launcher.py"
    
    # Define app name
    app_name = "AIDevIDE"
    
    # Clean previous builds
    print("🧹 Cleaning previous build artifacts...")
    for folder in ['build', 'dist']:
        if os.path.exists(folder):
            shutil.rmtree(folder)
    if os.path.exists(f"{app_name}.spec"):
        os.remove(f"{app_name}.spec")

    # Prepare PyInstaller arguments
    args = [
        entry_point,
        "--name=%s" % app_name,
        "--onefile",
        "--windowed", # No console window
        "--clean",
        # Include data folders
        "--add-data=DoneSound;DoneSound",
        "--add-data=gui;gui",
        "--add-data=core;core",
        "--add-data=agents;agents",
        "--add-data=utils;utils",
        "--add-data=github;github",
        "--add-data=plugins;plugins",
        # Hidden imports that might be missed
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtGui",
        "--hidden-import=PySide6.QtWidgets",
        "--hidden-import=PySide6.QtPrintSupport",
        "--hidden-import=pygments.lexers.python",
        "--hidden-import=pygments.lexers.javascript",
        "--hidden-import=pygments.lexers.html",
        "--hidden-import=pygments.lexers.css",
        "--hidden-import=pygments.lexers.bash",
        "--hidden-import=pygments.lexers.markdown",
        # Exclude unnecessary modules to reduce size
        "--exclude-module=matplotlib",
        "--exclude-module=notebook",
        "--exclude-module=scipy.spatial.transform._rotation_groups",
        "--exclude-module=PySide6.QtWebEngine",
        "--exclude-module=PySide6.QtWebEngineCore",
        "--exclude-module=PySide6.QtWebEngineWidgets",
        "--exclude-module=PySide6.Qt3D",
        "--exclude-module=PySide6.QtCharts",
        "--exclude-module=PySide6.QtDataVisualization",
        "--exclude-module=PySide6.QtDesigner",
        "--exclude-module=PySide6.QtHelp",
        "--exclude-module=PySide6.QtMultimedia",
        "--exclude-module=PySide6.QtMultimediaWidgets",
        "--exclude-module=PySide6.QtVirtualKeyboard",
        "--exclude-module=PySide6.QtTest",
        "--exclude-module=PySide6.QtSql",
        "--exclude-module=PySide6.QtXml",
         "--exclude-module=unittest",
         "--exclude-module=pytest",
         "--exclude-module=IPython",
         # Collect all submodules for tricky packages
         "--collect-all=tkterminal",
        "--collect-all=pynput",
        "--collect-all=bitsandbytes",
    ]
    
    # Handle icon if exists (e.g., app.ico)
    if os.path.exists("app.ico"):
        args.append("--icon=app.ico")
        
    print(f"🚀 Starting build process for {app_name}...")
    
    try:
        PyInstaller.__main__.run(args)
        print(f"\n✅ Build successful! Executable can be found in the 'dist' folder.")
    except Exception as e:
        print(f"\n❌ Build failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build()

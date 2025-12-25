#!/usr/bin/env python3
"""
Launcher for AI Dev IDE
"""
import os
import sys
import subprocess
import logging
import time
from utils import get_resource_path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the current directory or MEIPASS to the Python path
if getattr(sys, 'frozen', False):
    sys.path.insert(0, sys._MEIPASS)
else:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main_launcher():
    """Main entry point for the launcher."""
    try:
        logger.info("Starting AI Dev IDE...")
        
        logger.info(f"Current directory: {os.getcwd()}")
        
        # Hardware detection
        try:
            from utils.hardware_info import get_gpu_info
            gpu = get_gpu_info()
            if gpu["has_nvidia"]:
                logger.info(f"🚀 Hardware: {gpu['details']}")
                if gpu["cuda_available"]:
                    logger.info("✅ CUDA acceleration is available for local models.")
            else:
                logger.info("ℹ️ Hardware: Using CPU (No NVIDIA GPU detected)")
        except Exception as e:
            logger.warning(f"Hardware check skipped: {e}")

        # Standard launch (Tkinter-based Main IDE)
        # We skip the PySide placeholder by default as it's not the main application
        try:
            logger.info("Launching AI Dev IDE (Tkinter)...")
            from app import main
            main()
        except Exception as e:
            logger.critical(f"Failed to launch main application: {e}")
            
            # Fallback to PySide only if Tkinter fails (unlikely)
            logger.info("Attempting fallback to PySide GUI...")
            try:
                import importlib.util
                spec6 = importlib.util.find_spec("PySide6")
                spec2 = importlib.util.find_spec("PySide2")
                if spec6 or spec2:
                    from gui.pyside_app import launch
                    app = launch()
                    sys.exit(app.exec())
            except Exception as e2:
                logger.error(f"Fallback also failed: {e2}")
                raise e
    except Exception as e:
        logger.critical(f"Critical error in launcher: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main_launcher()

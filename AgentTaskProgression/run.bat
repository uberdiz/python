@echo off
echo 🚀 Starting AI Dev IDE...

rem Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed! Please install Python 3.10+ from python.org
    pause
    exit /b
)

rem Setup virtual environment if it doesn't exist
if not exist ".venv" (
    echo 📦 Creating virtual environment...
    python -m venv .venv
)

rem Activate and run
echo 🛠️ Preparing environment...
call .venv\Scripts\activate

rem Check for NVIDIA GPU to install proper PyTorch
nvidia-smi >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ NVIDIA GPU detected. Installing CUDA-enabled PyTorch...
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
)

echo 📦 Checking dependencies...
pip install -r requirements.txt

echo ✨ Launching...
python launcher.py
pause

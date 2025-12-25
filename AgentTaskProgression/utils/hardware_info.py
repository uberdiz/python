import subprocess
import os
import platform
import logging

logger = logging.getLogger(__name__)

def get_gpu_info():
    """Detect NVIDIA GPU and CUDA availability."""
    gpu_info = {
        "has_nvidia": False,
        "cuda_available": False,
        "details": "No NVIDIA GPU detected."
    }
    
    try:
        if platform.system() == "Windows":
            # Check for nvidia-smi
            try:
                result = subprocess.run(['nvidia-smi', '--query-gpu=name,driver_version,memory.total', '--format=csv,noheader'], 
                                     capture_output=True, text=True, check=True)
                if result.stdout:
                    gpu_info["has_nvidia"] = True
                    gpu_info["details"] = result.stdout.strip()
                    # If nvidia-smi works, usually CUDA is available at driver level
                    gpu_info["cuda_available"] = True
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
                
        elif platform.system() == "Linux":
            if os.path.exists("/proc/driver/nvidia/version"):
                gpu_info["has_nvidia"] = True
                try:
                    result = subprocess.run(['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'], 
                                         capture_output=True, text=True)
                    gpu_info["details"] = result.stdout.strip()
                    gpu_info["cuda_available"] = True
                except:
                    gpu_info["details"] = "NVIDIA driver found but nvidia-smi failed."
                    
    except Exception as e:
        logger.error(f"Error detecting GPU: {e}")
        
    # Check for PyTorch CUDA if available
    try:
        import torch
        gpu_info["cuda_available"] = torch.cuda.is_available()
        if gpu_info["cuda_available"]:
            gpu_info["has_nvidia"] = True
            gpu_info["details"] = f"PyTorch detected: {torch.cuda.get_device_name(0)}"
            # Verify CUDA capability
            vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            gpu_info["vram_gb"] = round(vram, 2)
            if vram < 6:
                logger.warning(f"⚠️ Low VRAM detected ({gpu_info['vram_gb']} GB). Large models may be slow or fail.")
    except ImportError:
        pass
    except Exception as e:
        logger.debug(f"PyTorch CUDA check failed: {e}")
        
    return gpu_info

def enable_cuda_for_local_inference():
    """Returns a dictionary of environment variables or parameters to enable CUDA."""
    info = get_gpu_info()
    if info["cuda_available"]:
        logger.info(f"🚀 CUDA detected: {info['details']}. Enabling GPU acceleration for local models.")
        # For Ollama, it's automatic. For other libraries, we might return a device string.
        return {"device": "cuda", "use_gpu": True}
    else:
        logger.info("ℹ️ No CUDA-capable GPU found. Using CPU for local inference.")
        return {"device": "cpu", "use_gpu": False}

if __name__ == "__main__":
    print(get_gpu_info())

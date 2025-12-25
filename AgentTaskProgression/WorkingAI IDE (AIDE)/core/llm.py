"""
LLM Interface - Simplified with OpenAI focus
"""
import requests
import json
import os
import time
from typing import List, Dict
try:
    from huggingface_hub import InferenceClient, list_models
    HAS_HF = True
except Exception:
    HAS_HF = False

def call_llm(prompt, api_url, model, api_provider="openai", token=None, stop_event=None, **kwargs):
    """
    Call LLM - Simplified for OpenAI
    
    Args:
        prompt: The prompt to send
        api_url: API endpoint URL
        model: Model name
        api_provider: "openai", "ollama", or "huggingface"
        token: API token (OpenAI API key)
        stop_event: threading.Event to check for cancellation
        **kwargs: Additional parameters
        
    Returns:
        Generated text response
    """
    if stop_event and stop_event.is_set():
        return "Error: Task cancelled by user."

    if api_provider == "openai":
        return call_openai(prompt, api_url, model, token, stop_event=stop_event, **kwargs)
    elif api_provider == "ollama":
        return call_ollama(prompt, api_url, model, stop_event=stop_event, **kwargs)
    elif api_provider == "huggingface":
        return call_huggingface(prompt, api_url, model, token, stop_event=stop_event, **kwargs)
    elif api_provider == "anthropic":
        return call_anthropic(prompt, api_url, model, token, stop_event=stop_event, **kwargs)
    elif api_provider == "google":
        return call_gemini(prompt, api_url, model, token, stop_event=stop_event, **kwargs)
    else:
        raise ValueError(f"Unsupported provider: {api_provider}")

def call_openai(prompt, api_url, model, token, stop_event=None, **kwargs):
    """Call OpenAI API - WORKING VERSION"""
    if stop_event and stop_event.is_set():
        return "Error: Task cancelled by user."
    if not token:
        return "Error: OpenAI API key required. Get one at platform.openai.com/api-keys"
    
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Use the provided API URL or default to OpenAI
        if not api_url or api_url == "":
            api_url = "https://api.openai.com/v1/chat/completions"
        
        # Allow overrides via kwargs
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 512)
        system_prompt = kwargs.get("system_prompt", "You are a helpful AI coding assistant. Provide clear, concise code and explanations.")

        # Prepare payload: handle string vs list of messages
        if isinstance(prompt, list):
            messages = list(prompt) # Create a copy
            # Ensure system prompt is present if it's not already in history
            if not any(m.get("role") == "system" for m in messages):
                messages.insert(0, {"role": "system", "content": system_prompt})
        else:
            # Prepare content with optional images
            user_content = []
            if kwargs.get("images"):
                user_content.append({"type": "text", "text": prompt})
                for img_b64 in kwargs.get("images"):
                    user_content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}
                    })
            else:
                user_content = prompt

            messages = [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_content
                }
            ]

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": 0.95
        }
        
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=kwargs.get("timeout", 20)
        )
        
        if response.status_code == 200:
            result = response.json()
            choices = result.get("choices", [])
            
            if choices and len(choices) > 0:
                choice = choices[0]
                message = choice.get("message", {})
                
                if isinstance(message, dict):
                    return message.get("content", "").strip()
                elif isinstance(message, str):
                    return message.strip()
                else:
                    return str(choice)
            
            return str(result)
            
        elif response.status_code == 401:
            return "Error: Invalid API key. Please check your OpenAI API key."
            
        elif response.status_code == 429:
            return "Error: Rate limit exceeded. Please try again later."
            
        elif response.status_code == 400:
            error_data = response.json()
            error_msg = error_data.get("error", {}).get("message", "")
            return f"Error: {error_msg}"
            
        else:
            return f"Error {response.status_code}: {response.text[:200]}"
            
    except requests.exceptions.ConnectionError:
        return "Error: Could not connect to OpenAI API. Check your internet connection."
    except Exception as e:
        return f"Error: {str(e)}"

def call_anthropic(prompt, api_url, model, token, stop_event=None, **kwargs):
    """Call Anthropic Claude Messages API"""
    if stop_event and stop_event.is_set():
        return "Error: Task cancelled by user."
    if not token:
        return "Error: Anthropic API key required"
    try:
        headers = {
            "x-api-key": token,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 512)
        system_prompt = kwargs.get("system_prompt", "You are a helpful AI assistant.")
        # Prepare content with optional images
        user_content = []
        if kwargs.get("images"):
            user_content.append({"type": "text", "text": prompt})
            for img_b64 in kwargs.get("images"):
                user_content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": img_b64
                    }
                })
        else:
            user_content = [{"type": "text", "text": prompt}]

        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "user", "content": user_content}
            ],
            "system": system_prompt,
            "temperature": temperature
        }
        endpoint = api_url or "https://api.anthropic.com/v1/messages"
        response = requests.post(endpoint, headers=headers, json=payload, timeout=kwargs.get("timeout", 20))
        if response.status_code == 200:
            data = response.json()
            try:
                content = data.get("content", [])
                if content and isinstance(content, list):
                    for part in content:
                        if part.get("type") == "text":
                            return part.get("text", "").strip()
                # Fallback to string conversion
                return json.dumps(data)[:1000]
            except Exception:
                return response.text[:1000]
        elif response.status_code == 401:
            return "Error 401: Invalid Anthropic API key"
        else:
            return f"Error {response.status_code}: {response.text[:200]}"
    except Exception as e:
        return f"Error: {str(e)}"

def call_gemini(prompt, api_url, model, token, stop_event=None, **kwargs):
    """Call Google Gemini Generative Language API"""
    if stop_event and stop_event.is_set():
        return "Error: Task cancelled by user."
    if not token:
        return "Error: Google API key required"
    try:
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 512)
        system_prompt = kwargs.get("system_prompt", "You are a helpful AI assistant.")
        endpoint_base = (api_url or "https://generativelanguage.googleapis.com/v1/models").rstrip("/")
        endpoint = f"{endpoint_base}/{model}:generateContent?key={token}"
        # Prepare parts with optional images
        parts = [{"text": prompt}]
        if kwargs.get("images"):
            for img_b64 in kwargs.get("images"):
                parts.append({
                    "inlineData": {
                        "mimeType": "image/jpeg",
                        "data": img_b64
                    }
                })

        payload = {
            "contents": [
                {"role": "user", "parts": parts}
            ],
            "systemInstruction": {"role": "system", "parts": [{"text": system_prompt}]},
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "topP": 0.95
            }
        }
        response = requests.post(endpoint, headers={"Content-Type": "application/json"}, json=payload, timeout=kwargs.get("timeout", 20))
        if response.status_code == 200:
            data = response.json()
            try:
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    for part in parts:
                        if "text" in part:
                            return part["text"].strip()
                return json.dumps(data)[:1000]
            except Exception:
                return response.text[:1000]
        elif response.status_code == 401:
            return "Error 401: Invalid Google API key"
        elif response.status_code == 400:
            try:
                err = response.json().get("error", {}).get("message", "")
                if err:
                    return f"Error 400: {err}"
            except Exception:
                pass
            return f"Error 400: {response.text[:200]}"
        elif response.status_code == 404:
            return "Error 404: Gemini model or endpoint not found"
        else:
            return f"Error {response.status_code}: {response.text[:200]}"
    except Exception as e:
        return f"Error: {str(e)}"

def call_ollama(prompt, api_url, model, stop_event=None, **kwargs):
    """Call Ollama API - Simplified with chat support"""
    if stop_event and stop_event.is_set():
        return "Error: Task cancelled by user."
    try:
        system_prompt = kwargs.get("system_prompt", "You are a helpful AI assistant.")
        # Hardware-aware options
        options = {
            "temperature": 0.7,
            "top_p": 0.9,
            "num_ctx": 8192,
        }
        
        try:
            from utils.hardware_info import get_gpu_info
            gpu = get_gpu_info()
            if gpu.get("cuda_available"):
                # Ollama uses num_gpu to control GPU offloading. 
                # Force high number to offload all layers
                options["num_gpu"] = 99
                # Lower thread count on GPU to avoid CPU overhead
                options["num_thread"] = 2
            else:
                import multiprocessing
                options["num_thread"] = max(1, multiprocessing.cpu_count() - 2)
        except:
            pass

        # Check if we should use chat API
        if isinstance(prompt, list):
            messages = list(prompt) # Create a copy
            if not any(m.get("role") == "system" for m in messages):
                messages.insert(0, {"role": "system", "content": system_prompt})
            
            endpoint = f"{api_url.rstrip('/')}/api/chat"
            payload = {
                "model": model,
                "messages": messages,
                "stream": False,
                "options": options
            }
        else:
            endpoint = f"{api_url.rstrip('/')}/api/generate"
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": options
            }
        
        if kwargs.get("images"):
            # For /api/generate it's "images", for /api/chat it's within messages (handled if list)
            if not isinstance(prompt, list):
                payload["images"] = kwargs.get("images")
        
        # Keep model in VRAM
        payload["keep_alive"] = "10m"
        
        response = requests.post(endpoint, json=payload, timeout=kwargs.get("timeout", 120))
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(prompt, list):
                return data.get("message", {}).get("content", "").strip()
            return data.get("response", "").strip()
        else:
            return f"Error {response.status_code}: {response.text[:200]}"
            
    except Exception as e:
        return f"Error: {str(e)}"

def call_huggingface(prompt, api_url, model, token, stop_event=None, **kwargs):
    """Call Hugging Face with robust fallback: provider-resolved router, client, alternatives."""
    if stop_event and stop_event.is_set():
        return "Error: Task cancelled by user."
    if not token:
        token = os.environ.get("HF_TOKEN", "")
    
    # Check if this is a local model request
    is_local = "localhost" in str(api_url) or "127.0.0.1" in str(api_url) or not api_url
    
    if is_local:
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
            return call_local_transformers(prompt, model, stop_event=stop_event, **kwargs)
        except ImportError:
            _hf_log("Local inference requested but 'torch' or 'transformers' not installed. Falling back to API.")
        except Exception as e:
            _hf_log(f"Local inference failed: {e}. Falling back to API.")

    if not token and not is_local:
        return "Error: Hugging Face token required for remote API"

    temperature = kwargs.get("temperature", 0.7)
    max_tokens = kwargs.get("max_tokens", 500)
    system_prompt = kwargs.get("system_prompt", "You are a helpful AI assistant.")

    # Hardware-aware options for potential local inference
    try:
        from utils.hardware_info import get_gpu_info
        gpu = get_gpu_info()
        # If api_url is local and we have GPU, we might want to signal it, 
        # though usually the local server (TGI/vLLM) handles it.
        # But for documentation/logging, it's good to know.
        if gpu.get("cuda_available") and ("localhost" in str(api_url) or "127.0.0.1" in str(api_url)):
            _hf_log("Local Hugging Face endpoint detected with CUDA available.")
    except:
        pass

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Heuristic: some models are not chat-completions capable; prefer inference route
    non_chat_patterns = [
        "starcoder", "bigcode", "codellama", "llama-2", "gpt2", "bloom", "mpt", "phi", "rwkv"
    ]

    # Prepare messages for chat completions (moved up to avoid NameError)
    if isinstance(prompt, list):
        messages_chat = list(prompt)
        if not any(m.get("role") == "system" for m in messages_chat):
            messages_chat.insert(0, {"role": "system", "content": system_prompt})
    else:
        messages_chat = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]

    # Simple response cache
    global _HF_RESP_CACHE
    try:
        _HF_RESP_CACHE
    except NameError:
        _HF_RESP_CACHE = {}
    
    # Ensure prompt is hashable for cache key
    if isinstance(prompt, list):
        cache_prompt = str(prompt)[:500]
    else:
        cache_prompt = str(prompt)[:500]
    
    # Ensure model is hashable
    hashable_model = str(model) if isinstance(model, list) else model
    
    # Also ensure max_tokens and temperature are numbers
    try:
        max_tokens_val = int(max_tokens)
    except:
        max_tokens_val = 500
        
    try:
        temp_val = float(temperature)
    except:
        temp_val = 0.7
        
    cache_key = (hashable_model, cache_prompt, max_tokens_val, round(temp_val, 2))
    cache_entry = _HF_RESP_CACHE.get(cache_key)
    if cache_entry and (time.time() - cache_entry[0] < 60):
        return cache_entry[1]

    # Direct Inference API attempt for custom models
    try:
        # If model looks like a full repo ID (contains /), try direct inference first
        if "/" in str(model):
            direct_endpoint = f"https://api-inference.huggingface.co/models/{model}"
            
            # Use simple text generation for non-chat models
            if any(p in (model or "").lower() for p in non_chat_patterns):
                payload_direct = {
                    "inputs": prompt if isinstance(prompt, str) else "\n".join([f"{m.get('role', 'user')}: {m.get('content', '')}" for m in prompt]),
                    "parameters": {"max_new_tokens": max_tokens, "temperature": temperature}
                }
            else:
                # Try chat completions format on direct endpoint
                payload_direct = {
                    "model": model,
                    "messages": messages_chat,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }

            r_direct = requests.post(direct_endpoint, headers=headers, json=payload_direct, timeout=kwargs.get("timeout", 20))
            if stop_event and stop_event.is_set():
                return "Error: Task cancelled by user."
            if r_direct.status_code == 200:
                data = r_direct.json()
                if isinstance(data, list) and data:
                    text = data[0].get("generated_text", "")
                    if text:
                        _HF_RESP_CACHE[cache_key] = (time.time(), text)
                        return text
                elif isinstance(data, dict):
                    # Check for chat completion response
                    choices = data.get("choices", [])
                    if choices:
                        out = choices[0].get("message", {}).get("content", "").strip()
                        if out:
                            _HF_RESP_CACHE[cache_key] = (time.time(), out)
                            return out
                    # Check for direct text
                    out = data.get("generated_text", "")
                    if out:
                        _HF_RESP_CACHE[cache_key] = (time.time(), out)
                        return out
    except Exception:
        pass

    try:
        if any(p in (model or "").lower() for p in non_chat_patterns):
            # If prompt is a list (history), join it for non-chat inference
            infer_prompt = prompt
            if isinstance(prompt, list):
                infer_prompt = "\n".join([f"{m.get('role', 'user')}: {m.get('content', '')}" for m in prompt])

            payload_infer = {
                "inputs": infer_prompt,
                "parameters": {
                    "max_new_tokens": max_tokens,
                    "temperature": temperature
                }
            }
            endpoint = f"https://router.huggingface.co/models/{model}"
            if stop_event and stop_event.is_set():
                return "Error: Task cancelled by user."
            response = requests.post(endpoint, headers=headers, json=payload_infer, timeout=kwargs.get("timeout", 20))
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and result:
                    item = result[0]
                    if isinstance(item, dict) and "generated_text" in item:
                        text = item["generated_text"]
                        if text.startswith(str(infer_prompt)):
                            text = text[len(str(infer_prompt)):].strip()
                        _HF_RESP_CACHE[cache_key] = (time.time(), text)
                        return text
                return str(result)[:500]
            # If this fails, continue to normal flow
    except Exception:
        pass

    # If api_url provided, try it. If it looks like standard HF inference, append model
    try:
        if api_url:
            endpoint = api_url
            if ("api-inference.huggingface.co/models/" in api_url or "router.huggingface.co/models/" in api_url) and model not in api_url:
                endpoint = f"{api_url.rstrip('/')}/{model}"
            
            # Prepare messages: handle string vs list of messages
            if isinstance(prompt, list):
                messages = list(prompt) # Create a copy to avoid modifying the original list
                # Ensure there is a system message if needed
                if not any(m.get("role") == "system" for m in messages):
                    messages.insert(0, {"role": "system", "content": system_prompt})
            else:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]

            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": 0.95
            }
            if stop_event and stop_event.is_set():
                return "Error: Task cancelled by user."
            resp = requests.post(endpoint, headers=headers, json=payload, timeout=kwargs.get("timeout", 20))
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    msg = choices[0].get("message", {})
                    if isinstance(msg, dict):
                        out = (msg.get("content") or "").strip()
                        _HF_RESP_CACHE[cache_key] = (time.time(), out)
                        return out
                return str(data)[:500]
            if resp.status_code in (401, 429, 500, 503):
                _hf_log(f"Direct URL error {resp.status_code}; fallback engaged")
            elif resp.status_code == 404:
                _hf_log("Direct URL 404; verifying provider path and model id; continuing")
            else:
                return f"Error {resp.status_code}: {resp.text[:200]}"
    except requests.exceptions.ConnectionError:
        _hf_log("Connection error on direct URL; continuing")
    except Exception:
        pass

    # Role-aware routing preferences
    role = (kwargs.get("role") or "").lower()
    task_kw = (kwargs.get("task", "chat") or "chat").lower()
    resolved_task = "conversational" if task_kw == "chat" else "text-generation"

    def _hf_provider_preference(task: str, role_hint: str) -> List[str]:
        if role_hint in ("coder", "gui_coder"):
            return ["hf-inference", "together", "cerebras", "fal-ai", "featherless-ai"]
        if role_hint in ("tester",):
            return ["featherless-ai", "hf-inference", "cerebras", "together", "fal-ai"]
        if role_hint in ("image_agent", "vision"):
            return ["hf-inference", "fal-ai", "together", "cerebras", "featherless-ai"]
        if role_hint in ("planner", "architect"):
            return ["cerebras", "featherless-ai", "hf-inference", "together", "fal-ai"]
        return ["cerebras", "featherless-ai", "hf-inference", "fal-ai", "together"]
    def _resolve_model_with_provider(mid: str) -> str:
        try:
            u = f"https://huggingface.co/api/models/{mid}?expand=inferenceProviderMapping"
            r = requests.get(u, headers=headers, timeout=10)
            if r.status_code == 200:
                mp = r.json().get("inferenceProviderMapping", {})
                if isinstance(mp, dict) and mp:
                    pref = _hf_provider_preference(resolved_task, role)
                    for pname in pref:
                        info = mp.get(pname)
                        if isinstance(info, dict) and info.get("status") == "live" and info.get("task") == resolved_task:
                            return f"{mid}:{pname}"
                    for name, info in mp.items():
                        if info.get("status") == "live":
                            return f"{mid}:{name}"
                    return f"{mid}:{next(iter(mp.keys()))}"
        except Exception:
            pass
        return mid
    resolved_model = _resolve_model_with_provider(model)
    try:
        url = "https://router.huggingface.co/v1/chat/completions"
        payload_chat = {
            "model": resolved_model,
            "messages": messages_chat,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        # Only add top_p if explicitly requested and < 1.0, or use a safe default
        tp = kwargs.get("top_p", 0.9)
        if tp and tp < 1.0:
            payload_chat["top_p"] = tp
        
        if stop_event and stop_event.is_set():
            return "Error: Task cancelled by user."
        r = requests.post(url, headers=headers, json=payload_chat, timeout=kwargs.get("timeout", 20))
        if r.status_code == 200:
            data = r.json()
            choices = data.get("choices", [])
            if choices:
                msg = choices[0].get("message", {})
                if isinstance(msg, dict):
                    out = (msg.get("content") or "").strip()
                    _HF_RESP_CACHE[cache_key] = (time.time(), out)
                    return out
            return str(data)[:500]
        elif r.status_code == 400:
            _hf_log(f"Router v1 400 Error: {r.text[:500]}")
            # Fallback to non-chat if it's a model support issue
            if "model_not_supported" in r.text or "not a chat model" in r.text.lower():
                try:
                    u = f"https://huggingface.co/api/models/{model}?expand=inferenceProviderMapping"
                    rr = requests.get(u, headers=headers, timeout=10)
                    if rr.status_code == 200:
                        mp = rr.json().get("inferenceProviderMapping", {})
                        if isinstance(mp, dict):
                            for name in mp.keys():
                                alt_payload = dict(payload_chat)
                                alt_payload["model"] = f"{model}:{name}"
                                ar = requests.post(url, headers=headers, json=alt_payload, timeout=kwargs.get("timeout", 20))
                                if ar.status_code == 200:
                                    data = ar.json()
                                    choices = data.get("choices", [])
                                    if choices:
                                        msg = choices[0].get("message", {})
                                        if isinstance(msg, dict):
                                            out = (msg.get("content") or "").strip()
                                            _HF_RESP_CACHE[cache_key] = (time.time(), out)
                                            return out
                                    return str(data)[:500]
                except Exception:
                    pass
        if r.status_code in (401, 404):
            _hf_log(f"Router v1 returned {r.status_code}; trying fallbacks")
    except Exception:
        pass

    if HAS_HF:
        try:
            client = InferenceClient(model=model, token=token, timeout=kwargs.get("timeout"))
            try:
                res = client.chat_completion(
                    messages=messages_chat,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                if hasattr(res, "choices") and res.choices:
                    msg = getattr(res.choices[0], "message", None)
                    content = getattr(msg, "content", None)
                    if isinstance(content, str):
                        out = content.strip()
                        _HF_RESP_CACHE[cache_key] = (time.time(), out)
                        return out
                    if isinstance(msg, dict):
                        out = (msg.get("content") or "").strip()
                        _HF_RESP_CACHE[cache_key] = (time.time(), out)
                        return out
            except Exception as e:
                _hf_log(f"HF chat-completions failed: {e}")
            try:
                txt = client.text_generation(
                    str(prompt),
                    temperature=temperature,
                    max_new_tokens=max_tokens,
                )
                if isinstance(txt, str):
                    prompt_str = str(prompt)
                    out = txt[len(prompt_str):].strip() if txt.startswith(prompt_str) else txt.strip()
                    _HF_RESP_CACHE[cache_key] = (time.time(), out)
                    return out
            except Exception as e:
                _hf_log(f"HF text-generation failed: {e}")
        except Exception as e:
            _hf_log(f"HF InferenceClient init failed: {e}")

    # Try provider-specific OpenAI-compatible routes
    candidates = [
        f"https://router.huggingface.co/hf-inference/models/{model}/v1/chat/completions",
        f"https://router.huggingface.co/fal-ai/models/{model}/v1/chat/completions",
    ]
    payload_chat_final = {
        "model": model,
        "messages": messages_chat,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    for url in candidates:
        try:
            r = requests.post(url, headers=headers, json=payload_chat_final, timeout=kwargs.get("timeout", 20))
            if r.status_code == 200:
                data = r.json()
                choices = data.get("choices", [])
                if choices:
                    msg = choices[0].get("message", {})
                    if isinstance(msg, dict):
                        return (msg.get("content") or "").strip()
                return str(data)[:500]
            if r.status_code in (401, 404):
                _hf_log(f"Provider {url} returned {r.status_code}; trying next")
                continue
            if r.status_code == 503:
                return "Error 503: Hugging Face router temporarily unavailable. Please retry."
        except requests.exceptions.ConnectionError:
            _hf_log(f"Connection error to {url}; trying next")
            continue
        except Exception:
            continue

    # Fallback: standard inference text generation route
    try:
        payload_infer = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": temperature
            }
        }
        endpoint = f"https://router.huggingface.co/models/{model}"
        response = requests.post(endpoint, headers=headers, json=payload_infer, timeout=kwargs.get("timeout", 20))
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and result:
                item = result[0]
                if isinstance(item, dict) and "generated_text" in item:
                        text = item["generated_text"]
                        prompt_str = str(prompt)
                        if text.startswith(prompt_str):
                            text = text[len(prompt_str):].strip()
                        _HF_RESP_CACHE[cache_key] = (time.time(), text)
                        return text
            return str(result)[:500]
        elif response.status_code == 404:
            _hf_log("Router endpoint 404; attempting alternative models")
        elif response.status_code == 401:
            return "Error 401: Invalid Hugging Face credentials"
        else:
            return f"Error {response.status_code}: {response.text[:200]}"
    except requests.exceptions.ConnectionError:
        return "Error: Could not connect to Hugging Face router. Check connectivity or try again later."
    except Exception as e:
        _hf_log(f"Final router error: {e}")

    # Model-level fallback
    task = kwargs.get("task", "chat")
    for alt in _hf_recommended(task):
        if alt == model:
            continue
        try:
            _hf_log(f"Trying fallback model: {alt}")
            return call_huggingface(prompt, api_url, alt, token, **kwargs)
        except Exception:
            continue
    return "Error: No working Hugging Face route found"

def test_llm_connection(api_provider, api_url, model, token=None):
    """Test LLM connection - Simplified"""
    test_prompt = "Hello! Respond with 'OK' and nothing else."
    
    try:
        if api_provider == "openai":
            if not token:
                return False, "OpenAI API key is required"
            
            # Use default OpenAI URL if not provided
            if not api_url or api_url == "":
                api_url = "https://api.openai.com/v1/chat/completions"
            
            response = call_openai(test_prompt, api_url, model, token)
            
            if response and "Error:" not in response:
                return True, f"✅ OpenAI connection successful! Response: {response}"
            else:
                return False, f"❌ OpenAI connection failed: {response}"
                
        elif api_provider == "ollama":
            response = call_ollama(test_prompt, api_url, model)
            if response and "Error:" not in response:
                return True, f"✅ Ollama connection successful! Response: {response}"
            else:
                return False, f"❌ Ollama connection failed: {response}"
                
        elif api_provider == "huggingface":
            if not token:
                return False, "Hugging Face token required"
            
            response = call_huggingface(test_prompt, api_url, model, token, task="chat", timeout=10)
            if response and "Error:" not in response:
                return True, f"✅ Hugging Face connection successful! Response: {response}"
            else:
                return False, f"❌ Hugging Face connection failed: {response}"
        elif api_provider == "anthropic":
            if not token:
                return False, "Anthropic API key required"
            response = call_anthropic(test_prompt, api_url, model, token)
            if response and "Error:" not in response:
                return True, f"✅ Anthropic connection successful! Response: {response}"
            else:
                return False, f"❌ Anthropic connection failed: {response}"
        elif api_provider == "google":
            if not token:
                return False, "Google API key required"
            response = call_gemini(test_prompt, api_url, model, token)
            if response and "Error:" not in response:
                return True, f"✅ Google Gemini connection successful! Response: {response}"
            else:
                return False, f"❌ Google Gemini connection failed: {response}"
        else:
            return False, f"Unknown provider: {api_provider}"
            
    except Exception as e:
        return False, f"Connection error: {str(e)}"

def call_local_transformers(prompt, model_id, stop_event=None, **kwargs):
    """
    Call local model using Hugging Face Transformers with CUDA optimizations.
    Implements user-recommended practices: device mapping, mixed precision, and VRAM management.
    """
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _hf_log(f"Using device: {device} for local inference with model {model_id}")
        
        # Load tokenizer and model
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        
        # Load model with quantization if VRAM is low (as suggested by user)
        model_kwargs = {
            "device_map": "auto",
            "torch_dtype": torch.float16 if device == "cuda" else torch.float32,
        }
        
        # Check for low VRAM
        if device == "cuda":
            vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            if vram_gb < 8:
                _hf_log(f"Low VRAM ({vram_gb:.1f}GB). Attempting 8-bit quantization.")
                model_kwargs["load_in_8bit"] = True
        
        model = AutoModelForCausalLM.from_pretrained(model_id, **model_kwargs)
        
        # Prepare prompt
        if isinstance(prompt, list):
            # Convert chat history to string
            full_prompt = ""
            for msg in prompt:
                full_prompt += f"{msg.get('role', 'user')}: {msg.get('content', '')}\n"
            full_prompt += "assistant: "
        else:
            full_prompt = prompt

        inputs = tokenizer(full_prompt, return_tensors="pt").to(device)
        
        if stop_event and stop_event.is_set():
            return "Error: Task cancelled by user."

        # Inference with Mixed Precision (user recommendation)
        with torch.no_grad():
            if device == "cuda":
                with torch.cuda.amp.autocast():
                    outputs = model.generate(
                        **inputs,
                        max_new_tokens=kwargs.get("max_tokens", 512),
                        temperature=kwargs.get("temperature", 0.7),
                        do_sample=True,
                        pad_token_id=tokenizer.eos_token_id
                    )
            else:
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=kwargs.get("max_tokens", 512),
                    temperature=kwargs.get("temperature", 0.7),
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id
                )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Strip the input prompt from response if model repeats it
        if response.startswith(full_prompt):
            response = response[len(full_prompt):].strip()
            
        return response

    except Exception as e:
        _hf_log(f"Local transformers error: {e}")
        return f"Error: Local model loading failed. {e}"

# --- HF utilities ---
HF_LOG_FILE = os.path.join(os.path.expanduser("~"), ".ai_dev_ide_hf.log")

def _hf_log(msg: str):
    try:
        line = f"[HF] {msg}"
        print(line)
        with open(HF_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line+"\n")
    except Exception:
        pass

def _hf_recommended(task: str) -> List[str]:
    defaults = {
        "chat": [
            "Qwen/Qwen2.5-7B-Instruct",
            "deepseek-ai/DeepSeek-Coder-V2-Lite",
            "meta-llama/Llama-3.2-11B-Vision-Instruct",
            "mistralai/Mistral-7B-Instruct-v0.3"
        ],
        "code": [
            "Qwen/Qwen2.5-Coder-32B-Instruct",
            "deepseek-ai/DeepSeek-Coder-V2-Lite",
            "bigcode/starcoder2-15b"
        ],
        "vision": [
            "Qwen/Qwen2-VL-7B-Instruct",
            "meta-llama/Llama-3.2-11B-Vision-Instruct"
        ]
    }
    out = defaults.get(task, defaults["chat"]).copy()
    if HAS_HF:
        try:
            for info in list_models(limit=5):
                mid = getattr(info, "modelId", None) or getattr(info, "id", None)
                if mid and mid not in out:
                    out.append(mid)
        except Exception:
            pass
    return out[:10]

def hf_model_catalog(task: str = "chat", limit: int = 20) -> List[dict]:
    """Parse/collect HF models and return metadata for recommendations."""
    out = []
    if HAS_HF:
        try:
            filt = {"pipeline_tag": "text-generation"}
            for info in list_models(filter=filt, limit=limit):
                meta = {
                    "model": getattr(info, "modelId", None) or getattr(info, "id", None),
                    "pipeline_tag": getattr(info, "pipeline_tag", ""),
                    "downloads": getattr(info, "downloads", 0),
                    "likes": getattr(info, "likes", 0),
                    "task": task,
                    "size": getattr(info, "sha", ""),
                }
                if meta["model"]:
                    out.append(meta)
        except Exception as e:
            _hf_log(f"Model catalog error: {e}")
    # Ensure defaults included
    for m in _hf_recommended(task):
        if not any(x["model"] == m for x in out):
            out.append({"model": m, "pipeline_tag": "text-generation", "downloads": 0, "likes": 0, "task": task, "size": ""})
    return out

def run_hf_diagnostics(model: str, token: str) -> Dict[str, str]:
    """Exercise both client and raw HTTP for testing and error scenarios."""
    results = {}
    try:
        # Invalid token
        r = call_huggingface("OK?", "", model, "invalid", task="chat", timeout=5)
        results["invalid_token"] = r
    except Exception as e:
        results["invalid_token"] = f"Error: {e}"
    try:
        # Network interruption simulated by impossible host
        url = "https://router.huggingface.co/hf-inference/models/INVALID/v1/chat/completions"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        payload = {"model": model, "messages": [{"role": "user", "content": "OK"}]}
        resp = requests.post(url, headers=headers, json=payload, timeout=5)
        results["raw_http_status"] = f"{resp.status_code}"
    except Exception as e:
        results["raw_http_status"] = f"Error: {e}"
    try:
        # Valid client path
        r = call_huggingface("Say OK", "", model, token, task="chat", timeout=10)
        results["client_call"] = r[:200]
    except Exception as e:
        results["client_call"] = f"Error: {e}"
    return results

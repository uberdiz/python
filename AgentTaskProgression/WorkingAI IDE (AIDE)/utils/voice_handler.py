import threading
import time

class VoiceHandler:
    def __init__(self):
        self.is_listening = False
        self.recognizer = None
        self.microphone = None
        self.available = False
        self.error_message = ""
        self.device_index = None
        
        try:
            import speech_recognition as sr
            self.sr = sr  # Store module reference
            self.recognizer = sr.Recognizer()
            try:
                self.microphone = sr.Microphone()
                self.available = True
            except Exception:
                try:
                    import sounddevice as sd
                    import numpy as np
                    self.sd = sd
                    self.np = np
                    self.available = True
                    self.microphone = None  # Use sounddevice path
                except Exception as e:
                    self.error_message = f"Voice init error: {e}"
        except ImportError:
            self.error_message = "speech_recognition library not installed. Please install it with: pip install SpeechRecognition sounddevice numpy"

    def get_device_list(self):
        """Return list of available microphone devices"""
        if not self.available:
            return []
        
        # Start with Windows Default
        names = ["Windows Default"]
        
        # SpeechRecognition devices
        try:
            sr_names = self.sr.Microphone.list_microphone_names() or []
            names.extend(sr_names)
        except Exception:
            pass
            
        # Sounddevice devices (prefix with SD:index)
        try:
            if hasattr(self, 'sd') and self.sd:
                devs = self.sd.query_devices()
                for i, d in enumerate(devs):
                    if d.get('max_input_channels', 0) > 0:
                        names.append(f"SD:{i} {d.get('name','Unknown')}")
        except Exception as e:
            self.error_message = f"Error listing devices: {e}"
        return names

    def set_device(self, index):
        """Set the microphone device index"""
        if not self.available:
            return False
        try:
            devices = self.get_device_list()
            if 0 <= index < len(devices):
                name = devices[index]
                if name == "Windows Default":
                    self.device_index = None
                    self.microphone = self.sr.Microphone() # Default mic
                    return True
                elif name.startswith("SD:"):
                    # Use sounddevice index
                    try:
                        self.device_index = int(name.split()[0].split(":")[1])
                    except Exception:
                        self.device_index = index
                    self.microphone = None
                    return True
                else:
                    # Use SpeechRecognition microphone (adjust index because of "Windows Default")
                    sr_idx = index - 1 
                    self.device_index = sr_idx
                    self.microphone = self.sr.Microphone(device_index=sr_idx)
                    return True
        except Exception as e:
            self.error_message = f"Error setting device: {e}"
            return False

    def start_listening(self, on_text_callback, on_status_callback=None):
        """
        Start listening in a background thread.
        on_text_callback: function(text) called when speech is recognized
        on_status_callback: function(status_text) called for updates
        """
        if not self.available:
            if on_status_callback:
                on_status_callback(f"Error: {self.error_message}")
            return

        if self.is_listening:
            return

        self.is_listening = True
        
        def listen_loop():
            try:
                if on_status_callback:
                    on_status_callback("Listening...")
                    
                if self.microphone is not None:
                    with self.microphone as source:
                        # Log ambient noise adjustment
                        if on_status_callback:
                            on_status_callback("Calibrating (Silencing)...")
                        self.recognizer.adjust_for_ambient_noise(source, duration=1.5)
                        self.recognizer.dynamic_energy_threshold = True
                        self.recognizer.energy_threshold = 400 # Initial sensible default
                        
                        while self.is_listening:
                            try:
                                # Update status with current energy levels if possible
                                if on_status_callback:
                                    status = f"Listening (Threshold: {int(self.recognizer.energy_threshold)})"
                                    on_status_callback(status)
                                
                                # Listen for audio
                                audio = self.recognizer.listen(source, timeout=2, phrase_time_limit=15)
                                if not self.is_listening: break
                                
                                if on_status_callback:
                                    on_status_callback("Processing...")
                                
                                try:
                                    # Try Google recognition first
                                    if on_status_callback:
                                        on_status_callback("Processing (Google)...")
                                    text = self.recognizer.recognize_google(audio)
                                    if text and on_text_callback:
                                        on_text_callback(text)
                                except self.sr.UnknownValueError:
                                    # Fallback to local sphinx if available and google fails
                                    if on_status_callback:
                                        on_status_callback("Processing (Local)...")
                                    try:
                                        text = self.recognizer.recognize_sphinx(audio)
                                        if text and on_text_callback:
                                            on_text_callback(text)
                                    except Exception as e:
                                        if on_status_callback:
                                            on_status_callback("Could not understand audio")
                                except self.sr.RequestError as e:
                                    # If network is the issue, try sphinx
                                    if on_status_callback:
                                        on_status_callback("API Offline, trying Local...")
                                    try:
                                        text = self.recognizer.recognize_sphinx(audio)
                                        if text and on_text_callback:
                                            on_text_callback(text)
                                    except Exception:
                                        if on_status_callback:
                                            on_status_callback(f"API Error: {e}")
                                
                                if on_status_callback:
                                    on_status_callback("Listening...")
                            except self.sr.WaitTimeoutError:
                                # This is normal when no one is speaking
                                continue
                            except Exception as e:
                                if on_status_callback:
                                    on_status_callback(f"Error: {e}")
                                if not self.is_listening: break
                else:
                    # Sounddevice fallback path
                    samplerate = 16000
                    duration = 5 # Record in 5s chunks
                    while self.is_listening:
                        try:
                            if on_status_callback:
                                on_status_callback("Listening...")
                            
                            rec = self.sd.rec(int(duration * samplerate), samplerate=samplerate, channels=1, dtype='float32')
                            # Check is_listening while recording
                            for _ in range(int(duration * 10)):
                                if not self.is_listening: break
                                time.sleep(0.1)
                            
                            if not self.is_listening:
                                self.sd.stop()
                                break
                                
                            self.sd.wait()
                            data = (rec.flatten() * 32767).astype(self.np.int16).tobytes()
                            audio = self.sr.AudioData(data, samplerate, 2)
                            
                            if on_status_callback:
                                on_status_callback("Processing...")
                            
                            try:
                                text = self.recognizer.recognize_google(audio)
                                if text and on_text_callback:
                                    on_text_callback(text)
                            except self.sr.UnknownValueError:
                                pass # No speech detected in this chunk
                            except Exception as e:
                                if on_status_callback:
                                    on_status_callback(f"Processing Error: {e}")
                        except Exception as e:
                            if on_status_callback:
                                on_status_callback(f"Recording Error: {e}")
                            time.sleep(1)
            except Exception as e:
                if on_status_callback:
                    on_status_callback(f"Critical Voice Error: {e}")
            finally:
                self.is_listening = False
                if on_status_callback:
                    on_status_callback("Stopped")

        self.thread = threading.Thread(target=listen_loop, daemon=True)
        self.thread.start()

    def stop_listening(self):
        self.is_listening = False

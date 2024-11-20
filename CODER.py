import speech_recognition as sr
import keyboard  # Import the keyboard module

microphone_index = 2
recognizer = sr.Recognizer()

# Function to start and stop listening based on Enter key press
def listen_for_speech():
    listening = False
    while True:
        # Wait for the Enter key to start or stop listening
        if keyboard.is_pressed('enter'):
            if not listening:
                print("Listening started... Press Enter again to stop.")
                listening = True
            else:
                print("Listening stopped.")
                break  # Exit the loop to stop listening
            
            # Wait for the Enter key to be released before checking again
            while keyboard.is_pressed('enter'):
                pass
        
        if listening:
            # Record audio when listening is active
            with sr.Microphone(device_index=microphone_index) as source:
                recognizer.adjust_for_ambient_noise(source)
                print("Say something...")
                audio = recognizer.listen(source)
                
                try:
                    print("You said: " + recognizer.recognize_google(audio))
                except sr.UnknownValueError:
                    print("Sorry, I couldn't understand what you said.")
                except sr.RequestError as e:
                    print(f"Could not request results from Google Speech Recognition service; {e}")
                
            listening = False  # Reset the listening flag after processing speech

# Call the function to start listening
listen_for_speech()

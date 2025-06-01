# Simulating Human Typing with Python Keyboard Module
import keyboard
import time
import random

# Text to be typed (not included here)
write = ""
# Split the text into words for procevying war against the ssing  Enter 
words = write.split()
keyboard.wait("ctrl+alt")
for word in words:
    if random.randint(0, 100) == 1: # 1% chance
        time.sleep(10)
    if random.randint(0, 1000) == 1: # .1% chance
        time.sleep(30)
    # Press the 'Enter' key when the word is exactly "Enter"
    if word == "Enter":
        keyboard.press_and_release('enter')
        if random.randint(0, 10) == 1: # 10% chance
            time.sleep(20)
        time.sleep(10)
        
    else:
            
        # Type the word character by character
        for i in word:
            # Add random pauses to simulate natural typing speed
            pause = random.uniform(0.1, 0.5)

            # Add longer pauses after periods, commas, and newlines
            if i == "." or i == ",":
                pause += random.uniform(0.2, 0.5)
            elif i == "\n":
                pause += random.uniform(0.5, 1.0)

            time.sleep(pause)

            # Random chance to simulate typo and backspace
            if random.randint(0, 100) < 8:  # 3% chance of typo
                # Typing a random number of wrong letters (1-3)
                typo_length = random.randint(1, 3)
                for _ in range(typo_length):
                    keyboard.write(random.choice("abcdefghijklmnopqrstuvwxyz"))
                    time.sleep(random.uniform(0.05, 0.15))
                
                # Pause to simulate the user realizing the mistake
                time.sleep(random.uniform(0.3, 0.6))
                
                # Backspace the typed letters (same number as typo_length)
                for _ in range(typo_length):
                    keyboard.press_and_release('backspace')
                    time.sleep(0.05)  # Brief delay between backspaces

            # Type each character normally
            keyboard.write(i)
        
        # Add a space between words
        keyboard.write(' ')

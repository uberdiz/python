# Simulating Human Typing with Python Keyboard Module
import keyboard
import time
import random

# Text to be typed (not included here)
write = "Battle of Trenton (December 26, 1776): Enter 1. The Battle of Trenton came about after popular George Washington's famous crossing of the icy Delaware River on Christmas night, 1776. Enter Washington led about 2,400 soldiers with intentions of a surprise attack in opposition to Hessian forces stationed in Trenton, New Jersey. Enter The Hessians, German mercenaries fighting for the British, have been stuck off guard due to the timing of the assault, the day after Christmas. Enter The Hessian commander, Colonel Johann Rall, had now not fortified the city as he underestimated the danger posed by Washington's forces. Enter The weather became brutal, with freezing rain, snow, and hail impacting both sides all through the struggle. Enter The battle lasted approximately 90 minutes, and it ended in a decisive victory for the Continental army. Enter Washington's forces captured almost 1,000 Hessians, whilst struggling only minimal casualties— American soldiers froze to death during the march. Enter The victory at Trenton boosted the morale of the Continental army and the American public. Enter This battle marked a turning point for the American Revolutionary War, as it demonstrated Washington's leadership and strategic abilities. Enter The victory at Trenton helped to inspire many American soldiers to re-enlist after their terms were set to expire at the end of the year. Enter Enter Battle of Princeton (January 3, 1777): Enter 11. The Battle of Princeton occurred shortly after the Battle of Trenton, as Washington sought to maintain momentum against British forces. Enter Washington and his army avoided British General Charles Cornwallis's attempt to trap them in Trenton by quietly marching overnight to Princeton. Enter The battle was fought between Washington's 5,000 men and around 1,200 British soldiers stationed at Princeton. Enter Washington's forces encountered British troops under the command of Colonel Charles Mawhood just outside of Princeton. Enter In the initial skirmish, the British forces had the upper hand, and several American militia units began to retreat. Enter Washington personally rallied his troops on the battlefield, riding his horse directly into the line of fire to encourage his men to fight on. Enter The American forces regrouped and launched a successful counterattack, driving the British back and forcing them to retreat. Enter The victory at Princeton resulted in around 450 British casualties, while the Americans suffered about 40 losses. Enter After the battle, Washington led his troops to winter quarters in Morristown, New Jersey, avoiding further conflict with larger British forces. Enter  The twin victories at Trenton and Princeton significantly boosted American morale and secured Washington's reputation as a capable military leader. Enter Enter Enter Fischer, David Hackett. *Washington's Crossing*. Oxford University Press, 2004."
# Split the text into words for processing
words = write.split()
time.sleep(10)
for word in words:
    # Press the 'Enter' key when the word is exactly "Enter"
    if word == "Enter":
        keyboard.press_and_release('enter')
    else:
        # Type the word character by character
        for i in word:
            # Add random pauses to simulate natural typing speed
            pause = random.uniform(0.05, 0.3)

            # Add longer pauses after periods, commas, and newlines
            if i == "." or i == ",":
                pause += random.uniform(0.2, 0.5)
            elif i == "\n":
                pause += random.uniform(0.5, 1.0)

            time.sleep(pause)

            # Random chance to simulate typo and backspace
            if random.randint(0, 100) < 3:  # 3% chance of typo
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

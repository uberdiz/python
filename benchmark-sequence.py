from selenium.webdriver.common.by import By
from selenium import webdriver
import time
import keyboard
import pyautogui

press = []
clicked = False
p1 = [830, 300]
p2 = [950, 300]
p3 = [1100, 300]
p4 = [830, 450]
p5 = [950, 450]
p6 = [1100, 450]
p7 = [830, 590]
p8 = [950, 590]
p9 = [1100, 590]

def click(press):
    print(press)
    time.sleep(0.8)
    for i in press:
        if i == 0:
            pyautogui.click(p1[0], p1[1])
        elif i == 1:
            pyautogui.click(p2[0], p2[1])
        elif i == 2:
            pyautogui.click(p3[0], p3[1])
        elif i == 3:
            pyautogui.click(p4[0], p4[1])
        elif i == 4:
            pyautogui.click(p5[0], p5[1])
        elif i == 5:
            pyautogui.click(p6[0], p6[1])
        elif i == 6:
            pyautogui.click(p7[0], p7[1])
        elif i == 7:
            pyautogui.click(p8[0], p8[1])
        elif i == 8:
            pyautogui.click(p9[0], p9[1])

def type_fast(driver):
    global clicked
    try:
        squares = driver.find_elements(By.CSS_SELECTOR, "div.square")
        active_indices = []
        for index, square in enumerate(squares):
            if "active" in square.get_attribute("class"):
                active_indices.append(index)
        if active_indices:
            for index in active_indices:
                if index not in press:
                    press.append(index)
            clicked = False
        elif not clicked:
            click(press)
            clicked = True
    except Exception as e:
        print(f"Error in type_fast: {e}")

def main():
    try:
        driver = webdriver.Chrome()  # Initialize the Chrome driver
        driver.get("https://humanbenchmark.com/tests/sequence")
        keyboard.wait("ctrl+shift")
        time.sleep(1)
        pyautogui.moveTo(960, 560, duration=1)
        pyautogui.click()
        coun = 0
        while coun < 100:
            type_fast(driver)
            coun += 1
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()

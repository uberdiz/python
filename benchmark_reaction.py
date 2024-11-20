from selenium.webdriver.common.by import By
import time
import keyboard
import undetected_chromedriver as uc
import pyautogui

def type_fast(driver):
    # Corrected CSS selector, assuming it's a class-based selector
    while True:
        frame = driver.find_elements(By.CSS_SELECTOR, "div.view-go.e18o0sx0.css-saet2v.e19owgy77")
        if frame:
            pyautogui.click()
            time.sleep(1000)
        else:
            continue

def main():
    driver = uc.Chrome()
    driver.get("https://humanbenchmark.com/tests/reactiontime")
    
    while True:
        keyboard.wait("ctrl+shift")
        pyautogui.moveTo(1000, 500, duration=1)
        pyautogui.click()
        
        while True:
            type_fast(driver)

if __name__ == "__main__":
    main()

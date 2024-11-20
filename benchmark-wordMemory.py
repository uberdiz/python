from selenium.webdriver.common.by import By
import time
import keyboard
import undetected_chromedriver as uc
import pyautogui

words = []
def type_fast(driver):
    elements = driver.find_element(By.CSS_SELECTOR, "div.word")
    if elements.text not in words:
        words.append(elements.text)
        print(words)
        # New elements
        pyautogui.moveTo(1000,500)
        pyautogui.click()
    else:
        # Old elements
        pyautogui.moveTo(900,500)
        pyautogui.click()
def main():
    counter = 0
    driver = uc.Chrome()
    driver.get("https://humanbenchmark.com/tests/verbal-memory")
    keyboard.wait("ctrl+shift")
    while True:
        pyautogui.moveTo(960, 560, duration=1)
        pyautogui.click()
        while counter < 5000:
            type_fast(driver)
            time.sleep(0.001)
            counter += 1
if __name__ == "__main__":
    main()

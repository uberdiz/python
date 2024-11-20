from selenium.webdriver.common.by import By
import time
import keyboard
import undetected_chromedriver as uc
import pyautogui

def type_fast(driver):
    elements = driver.find_elements(By.CSS_SELECTOR, "div.big-number")
    if elements:
        return elements[0].text  # Assuming you want the text of the first matching element
    else:
        return None
def typer(driver):
    elements = driver.find_elements(By.CSS_SELECTOR, "input")
    if elements:
        return True
    else:
        return False

def main():
    driver = uc.Chrome()
    driver.get("https://humanbenchmark.com/tests/number-memory")
    keyboard.wait("ctrl+alt+t")
    while True:
        pyautogui.moveTo(960, 560, duration=1)
        pyautogui.click()
        while True:
            number = type_fast(driver)
            time.sleep(0.0001)
            if number:
                break
        while True:
            type = typer(driver)
            time.sleep(0.0001)
            if type:
                break
        keyboard.write(number)
        keyboard.press_and_release('enter') 
        time.sleep(.5)
if __name__ == "__main__":
    main()

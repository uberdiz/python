from selenium.webdriver.common.by import By
import time
import keyboard
import random
import undetected_chromedriver as uc

def type_fast(driver):
    spans = driver.find_elements(By.CSS_SELECTOR, "span.incomplete")
    # Collect text content of each <span> element
    text_to_type = [span.text for span in spans]
    for i in text_to_type:
        if i:
            keyboard.write(i)
        else:
            keyboard.press_and_release('space')

def main():
    driver = uc.Chrome()
    driver.get("https://humanbenchmark.com/tests/typing")
    
    while True:
        keyboard.wait("ctrl+shift")
        type_fast(driver)
if __name__ == "__main__":
    main()

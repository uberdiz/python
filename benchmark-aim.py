from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import keyboard
import undetected_chromedriver as uc
import pyautogui

def type_fast(driver):
    while True:
        outer_div = driver.find_element(By.CLASS_NAME, "css-1k4dpwl")
        nested_div = outer_div.find_element(By.XPATH, ".//div[@style[contains(., 'transform: matrix3d')]]")
        transform_style = nested_div.get_attribute("style")

        matrix_values = transform_style.split("matrix3d(")[1].split(")")[0].split(", ")
        if matrix_values:
            x_coord = float(matrix_values[12]) + 450
            y_coord = float(matrix_values[13]) + 200
            return x_coord, y_coord
        else:
            continue
    
def main():
    driver = uc.Chrome()
    driver.get("https://humanbenchmark.com/tests/aim")
    while True:
        keyboard.wait("ctrl+shift")
        pyautogui.moveTo(960, 450, duration=1)
        pyautogui.click()
        counter = 0
        while counter != 30:
            x_coord, y_coord = type_fast(driver)
            if x_coord and y_coord:
                pyautogui.click(x_coord, y_coord)
                counter += 1

if __name__ == "__main__":
    main()

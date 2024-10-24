from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import pandas as pd

def scrape_yahoo(driver, stock):
    technicals = {}
    stock = stock.upper()
    url = f'https://finance.yahoo.com/quote/{stock}/key-statistics/'

    try:
        driver.get(url)

        # Use explicit wait instead of sleep
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table"))
        )

        # Get the page source and parse it
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        # ** Broad Search for Market Cap and other values **
        broad_search = soup.find_all('td')
        for item in broad_search:
            key = item.find_previous('td').text.strip() if item.find_previous('td') else None
            value = item.text.strip() if item else None
            if key and value and key not in technicals:  # Avoid overwriting keys
                technicals[key] = value

        # Get stock price
        price_search = soup.find_all('fin-streamer', {"class": "livePrice yf-1tejb6"})
        for item in price_search:
            key = "Price"
            value = item.text.strip("<span></span>") if item else None
            if key and value and key not in technicals:  # Avoid overwriting keys
                technicals[key] = value

        # Scrape Implied Volatility from the options page
        options_url = f'https://finance.yahoo.com/quote/{stock}/options?p={stock}'
        driver.get(options_url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table"))
        )

        options_soup = BeautifulSoup(driver.page_source, 'html.parser')
        # Scrape implied volatility from the options chain (assuming it's available)
        implied_vol_search = options_soup.find_all('td', text="Implied Volatility")
        for vol in implied_vol_search:
            key = "Implied Volatility"
            value = vol.find_next('td').text.strip() if vol.find_next('td') else None
            if key and value and key not in technicals:
                technicals[key] = value

        # Risk-Free Rate (10-year Treasury yield can be used as a proxy; fetch from external sources if needed)
        # For now, we'll use a placeholder value
        technicals['Risk-Free Rate'] = '4.5%'  # Example, you may want to scrape or fetch the real-time rate

    except Exception as e:
        print(f'Failed for stock {stock}, exception: {str(e)}')

    return technicals

def scrape(stock_list, interested):
    all_data = []  # Initialize a list to store the scraped data

    # Use a single driver instance for the whole scraping process
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run in headless mode
    driver = webdriver.Chrome(options=options)

    for each_stock in stock_list:
        technicals = scrape_yahoo(driver, each_stock)
        stock_data = {"Stock": each_stock.upper()}  # Start with the stock name

        for ind in interested:
            ind_stripped = ind.strip()  # Strip whitespace from the interested key
            stock_data[ind_stripped] = technicals.get(ind_stripped, 'Not found')  # Add the data or 'Not found'

        all_data.append(stock_data)  # Append the stock data dictionary to the list
        print(stock_data)  # Debug print
        print("------")
        time.sleep(1)  # Use delay to avoid getting flagged as a bot

    # Quit the driver after all stocks are scraped
    driver.quit()

    # Convert list of dictionaries into a DataFrame and save to CSV
    df = pd.DataFrame(all_data)
    df.to_csv('stock_data.csv', index=False)  # Save to CSV

def main():
    stock_list = ["AAPL", "NVDA", "MSFT", "TSLA", "AMZN", "GOOGL", "JNJ", "PG", "KO", "JPM", "BRKB.VI", "T", "XOM", "VZ", "AMD", "SHOP", "RIVN", "V", "MA", "WMT", "PEP", "PFE", "CSCO", "INTC", "DIS", "BA", "NKE"]
    interested = ['Market Cap', 'Price', 'Avg Vol (10 day) 3', 'Risk-Free Rate', 'Forward Annual Dividend Yield 4', 'Beta (5Y Monthly)']
    scrape(stock_list, interested)
import time
if __name__ == "__main__":
    a = time.time()
    main()
    b = time.time()
    print(f'Time taken: {b - a} seconds')  
    
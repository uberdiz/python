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
        price_search = soup.find_all('fin-streamer', {"class": "livePrice yf-1tejb6"})
        for item in price_search:
            key = "Price"
            value = item.text.strip("<span></span>") if item else None
            if key and value and key not in technicals:  # Avoid overwriting keys
                technicals[key] = value
            print(key, value)
        # ** Find tables with class 'table yf-vaowmx' for specific values **
        tables = soup.findAll('table', {"class": "table yf-vaowmx"})
        
        # Loop through tables and rows to get the data
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                col_name = row.find('span').text.strip() if row.find('span') else None
                col_val = row.find('td', {"class": "value yf-vaowmx"}).text.strip() if row.find('td', {"class": "value yf-vaowmx"}) else None
                if col_name and col_val:
                    technicals[col_name] = col_val  # Capture key-value pairs

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
        
        # Check if any of the values is '--' or 'Not found'
        #if any(technicals.get(ind.strip(), None) in ('Not found', '--') for ind in interested):
            #print(f"Skipping {each_stock} due to missing values.")
            #continue  # Skip to the next stock if any value is invalid

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
    df.to_csv('!StockHelper_List.csv', index=False)  # Save to CSV

def main():
    stock_list = ['CHSN', 'ALTM', 'AMD', 'TMUS', 'AXP', 'DECK', 'BRK-B', 'NVDA', 'TSLA', 'PLTR', 'F', 'JBLU', 'ABEV', 'SMCI', 'AMZN', 'JD', 'CCL', 'AAPL', 'IQ', 'WXXWY', 'MMYT', 'ANF', 'MNSO', 'FND', 'AMKBY', 'AZEK', 'NMRK', 'CWK', 'KIROY', 'EXR', 'UWMC', 'NSA']
    interested = ['Market Cap', 'Price/Sales', 'Price/Book', 'Return on Equity  (ttm)', 'Revenue  (ttm)', 'Quarterly Earnings Growth  (yoy)',
                  'Operating Cash Flow  (ttm)', 'Total Cash  (mrq)', 'Total Debt/Equity  (mrq)', 
                  'Current Ratio  (mrq)', '52 Week Range 3', 'Avg Vol (3 month) 3', 
                  'Avg Vol (10 day) 3', '% Held by Insiders 1', 'Diluted EPS  (ttm)', 'Levered Free Cash Flow  (ttm)', 'Forward Annual Dividend Yield 4', 'Trailing Annual Dividend Yield 3', '5 Year Average Dividend Yield 4', 'Price', 'Beta (5Y Monthly)']
    scrape(stock_list, interested)

if __name__ == "__main__":
    main()

from selenium import webdriver
from bs4 import BeautifulSoup
import time

def scrape_yahoo(stock):
    technicals = {}
    try:
        stock = stock.upper()
        url = f'https://finance.yahoo.com/quote/{stock}/key-statistics/'
        
        # Initialize Selenium WebDriver
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')  # Run in headless mode
        driver = webdriver.Chrome(options=options)
        driver.get(url)
        
        time.sleep(5)  # Allow some time for page to fully load
        
        # Get the page source and parse it
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()  # Close the driver

        # ** Broad Search for Market Cap and other values **
        broad_search = soup.find_all('td')  # Search for general values
        for item in broad_search:
            key = item.find_previous('td').text.strip() if item.find_previous('td') else None
            value = item.text.strip() if item else None
            if key and value and key not in technicals:  # Avoid overwriting keys
                technicals[key] = value
        
        # ** Find tables with class 'table yf-vaowmx' for specific values **
        tables = soup.findAll('table', {"class": "table yf-vaowmx"})
        
        # Loop through tables and rows to get the data
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                # Use more robust key extraction to avoid whitespace issues
                col_name = row.find('span').text.strip() if row.find('span') else None
                col_val = row.find('td', {"class": "value yf-vaowmx"}).text.strip() if row.find('td', {"class": "value yf-vaowmx"}) else None
                if col_name and col_val:
                    technicals[col_name] = col_val  # Capture key-value pairs
        
        # Print all captured statistics for the stock
        print(f"\nStatistics for {stock}:")
        for key, value in technicals.items():
            print(f"{key}: {value}")
        
        return technicals
    
    except Exception as e:
        print('Failed, exception:', str(e))
        return technicals

def scrape(stock_list):
    for each_stock in stock_list:
        scrape_yahoo(each_stock)
        print("------")
        time.sleep(1)  # Use delay to avoid getting flagged as a bot

def main():
    stock_list = ['aapl', 'tsla', 'ge']  # List of stock symbols to scrape
    scrape(stock_list)

if __name__ == "__main__":
    main()

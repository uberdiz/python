from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
stock_names = []
# Initialize the Selenium WebDriver (use ChromeDriver, ensure you have installed it)
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

# Open the Yahoo Finance Most Active Stocks page
url = "https://finance.yahoo.com/markets/stocks/most-active/?start=0&count=100"
driver.get(url)

# Wait for the page to load (you might adjust the sleep time depending on your connection)
time.sleep(5)

# Find all stock symbols by their class name
stock_symbols = driver.find_elements(By.CLASS_NAME, 'symbol.yf-1jpysdn')

# Extract and print stock symbols
for symbol in stock_symbols:
    symbol = symbol.text.upper()
    stock_names.append(symbol)

# Close the browser window
driver.quit()

def compare_stock(stock_names):
    compare_stock = ['CHSN', 'SOFI', 'ALTM', 'SHOP', 'AMD', 'TMUS', 'RIVN', 'SHOP.TO', 'RDDT', 'BENF', 'AXP', 'TIGR', 'FORD', 'ASTS', 'CDE', 'EH', 'OKLO', 'UBI.PA', 'TEAM', 'DECK', 'MSTR', 'GEV', 'LAC', 'BRK-B', 'DIDIY', 'NVDA', 'NIO', 'INND', 'TSLA', 'SWN', 'PLTR', 'EVGO', 'AAL', 'F', 'JBLU', 'ABEV', 'INTC', 'MARA', 'SMCI', 'AMZN', 'JD', 'CCL', 'AAPL', 'IQ', 'LCID', 'BAC', 'WXXWY', 'B', 'NFE', 'ENVX', 'CLSK', 'MMYT', 'WB', 'ASPN', 'VFC', 'ANF', 'NMRA', 'MNSO', 'CFLT', 'DOCN', 'ALB', 'TEM', 'ALAB', 'IOVA', 'ZIM', 'NVAX', 'FND', 'IRDM', 'AMKBY', 'AXSM', 'AZEK', 'NMRK', 'CWK', 'APGE', 'KIROY', 'EXR', 'UWMC', 'NSA', 'SMG', 'TTC', 'BEKE', 'BABA', 'T', 'PFE', 'PWSC', 'BBD', 'RLX', 'NU', 'RIG', 'MU', 'PDD', 'VALE', 'YMM', 'GRAB', 'RIOT', 'GOLD', 'WBD', 'JOBY', 'ITUB', 'XPEV', 'XOM', 'WBA', 'AGNC', 'FUTU', 'SNAP', 'META', 'BILI', 'AVGO', 'CVS', 'GOOGL', 'CLOV', 'KO', 'OXY', 'KGC', 'VST', 'NCLH', 'WFC', 'MSFT', 'VZ', 'WMT', 'PCG', 'FCX', 'GOOG', 'CVE', 'STLA', 'BTE', 'BTG', 'LI', 'HBAN', 'UBER', 'RKLB', 'AES', 'U', 'ET', 'LYG', 'NKE', 'BMY', 'JPM', 'UAL', 'EQT', 'NOK', 'PR', 'HL', 'DJT', 'MRK', 'BP', 'SLB', 'ERIC', 'TGT', 'O', 'MO', '^GSPC', 'CUK']
    for stock in stock_names:
        if stock not in compare_stock:
            compare_stock.append(stock)

    print(compare_stock)
compare_stock(stock_names)
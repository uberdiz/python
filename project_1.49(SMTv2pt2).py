import pandas as pd
import os
import SMTv2 as sm

# Load data from CSV (replace with actual file path if reading from a file)
df = pd.read_csv("!StockHelper_List.csv")

# Lists to store ranked stocks and stocks with incomplete data
complete_data_stocks = []
incomplete_data_stocks = []
swing_stocks = []
dividend_stocks = []
reload_stocks = []
interested = ['Market Cap', 'Price/Sales', 'Price/Book', 'Return on Equity  (ttm)', 'Revenue  (ttm)', 'Quarterly Earnings Growth  (yoy)', 'Operating Cash Flow  (ttm)', 'Total Cash  (mrq)', 'Total Debt/Equity  (mrq)', 'Current Ratio  (mrq)', '52 Week Range 3', 'Avg Vol (3 month) 3', 'Avg Vol (10 day) 3', '% Held by Insiders 1', 'Diluted EPS  (ttm)', 'Levered Free Cash Flow  (ttm)', 'Forward Annual Dividend Yield 4', 'Trailing Annual Dividend Yield 3', '5 Year Average Dividend Yield 4', 'Price', 'Beta (5Y Monthly)']
def load_existing_stocks():
    reload_stocks = []
    reload_stocks = pd.read_csv("stocks_to_buy.csv", usecols=['Stock'])
    reload_stocks = reload_stocks['Stock'].tolist()
    print(reload_stocks)
    sm.main(reload_stocks, interested)

    if os.path.exists("stocks_to_buy.csv"):
        return pd.read_csv("stocks_to_buy.csv", header=None, names=['Type', 'Stock', 'Price', 'Shares', 'Total_Invested'])
    return pd.DataFrame(columns=['Type', 'Stock', 'Price', 'Shares', 'Total_Invested'])
load_existing_stocks()
# Function to check if a row has missing or invalid data
def has_missing_data(row):
    return any(value in ['--', 'Not Found', ''] for value in row)

# Function to calculate stock score for swing trading (higher volatility, growth-oriented)
def score_swing_stock(row):
    try:
        # Weights for swing trading financial metrics (more focus on growth)
        weights = {
            'Return on Equity  (ttm)': 0.3,
            'Quarterly Earnings Growth  (yoy)': 0.3,
            'Operating Cash Flow  (ttm)': 0.2,
            'Price/Sales': 0.1,
            'Price/Book': 0.1,
            'Beta (5Y Monthly)': 0.05  # Assuming higher beta is better for swing trading
        }
        
        # Score calculation using columns
        score = 0
        for metric, weight in weights.items():
            value = row[metric]
            if isinstance(value, str):
                value = value.strip('%').replace('M', '').replace('B', '').replace('-', '')
                value = float(value) if value else 0.0  # Convert to float or set to 0 if empty
            score += value * weight
            
        return score
    except ValueError:
        return None  # Return None if score calculation fails

# Function to calculate stock score for dividend stocks (focus on stability and yield)
def score_dividend_stock(row):
    try:
        # Weights for dividend stocks (focus on dividends and stability)
        weights = {
            'Return on Equity  (ttm)': 0.2,
            'Quarterly Earnings Growth  (yoy)': 0.1,
            'Operating Cash Flow  (ttm)': 0.2,
            'Price/Sales': 0.1,
            'Price/Book': 0.1,
            'Forward Annual Dividend Yield 4': 0.3,  # Dividend yield gets a larger weight
            'Beta (5Y Monthly)': -0.05  # Lower beta is better for dividend stocks
        }
        
        # Score calculation using columns
        score = 0
        for metric, weight in weights.items():
            value = row[metric]
            if isinstance(value, str):
                #FIXME qweeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee
                value = value.strip('%').replace('M', '').replace('B', '').replace('-', '')
                value = float(value) if value else 0.0  # Convert to float or set to 0 if empty
            score += value * weight
            
        return score
    except ValueError:
        return None  # Return None if score calculation fails

# Iterate over each row in the DataFrame
for index, row in df.iterrows():
    if has_missing_data(row):
        incomplete_data_stocks.append({'Stock': row['Stock']})
    else:
        # Calculate scores for both categories
        swing_score = score_swing_stock(row)
        dividend_score = score_dividend_stock(row)
        if swing_score is not None:
            swing_stocks.append({
                'Stock': row['Stock'],
                'Score': swing_score,
                'Price': float(row['Price'])
            })
        if dividend_score is not None:
            dividend_stocks.append({
                'Stock': row['Stock'],
                'Score': dividend_score,
                'Price': float(row['Price'])
            })

# Sorting stocks by score
swing_stocks = sorted(swing_stocks, key=lambda x: x['Score'], reverse=True)
dividend_stocks = sorted(dividend_stocks, key=lambda x: x['Score'], reverse=True)

# Prepare buyer lists based on scores
swing_buyer = [stock['Score'] for stock in swing_stocks]
dividend_buyer = [stock['Score'] for stock in dividend_stocks]

# Total scores for calculating proportionate investment
total_swing_score = sum(swing_buyer)
total_dividend_score = sum(dividend_buyer)
total_spent = 0
top_n = 10  # Select top N stocks
# Function to calculate the sell decision for swing stocks
def calculate_sell_swing_stocks():
    existing_stocks = load_existing_stocks()
    
    # Filter only swing stocks from the existing stocks file
    swing_stocks_held = existing_stocks[existing_stocks['Type'] == 'Swing']
    
    if swing_stocks_held.empty:
        print("No swing stocks to evaluate for selling.")
        return

    print("\nEvaluating swing stocks for selling...")
    for index, row in swing_stocks_held.iterrows():
        stock_name = row['Stock']
        purchase_price = float(row['Price'])
        shares_held = int(row['Shares'])
        
        # Check the current price from the main data file (df)
        current_stock_data = df[df['Stock'] == stock_name]
        if not current_stock_data.empty:
            current_price = float(current_stock_data.iloc[0]['Price'])
            
            # Define the condition to sell (e.g., if price has increased by 7%)
            price_increase_threshold = 1.07 * purchase_price  # Sell if current price is 7% higher
            
            if current_price >= price_increase_threshold:
                total_value = shares_held * current_price
                print(f"Sell {shares_held} shares of {stock_name} at ${current_price:.2f} for a total of ${total_value:.2f}.")
            else:
                print(f"Hold {shares_held} shares of {stock_name}. Current price is ${current_price:.2f}, waiting for price increase.")
        else:
            print(f"Could not find current data for {stock_name}.")

# Calculate stocks to buy for both categories and write to CSV
def calculate_stocks(money, total_spent, swing_stocks, dividend_stocks, total_swing_score, total_dividend_score, top_n=None, action='buy'):
    swing_money = 0.3 * money  # 30% to swing trading (growth-focused)
    dividend_money = 0.7 * money  # 70% to dividend stocks (stability-focused)
    swing_ran = False
    
    # Open CSV for writing
    with open('stocks_to_buy.csv', 'a') as f:
        
        if action == 'buy':
            if money <= 10000:
                top_n = 5
                if money <= 1000:
                    top_n = 3
                    if money <= 500:
                        top_n = 1
            if swing_stocks:
                # Process swing trading stocks
                print(f"Buying Swing Trading Stocks with ${swing_money:.2f}\n")
                stocks_to_buy = swing_stocks[:top_n] if top_n else swing_stocks
                for stock in stocks_to_buy:
                    weight = stock['Score'] / total_swing_score
                    amount_to_invest = swing_money * weight
                    shares_to_buy = max(1, int(amount_to_invest // stock['Price']))  # Ensure it's a multiple of stock price
                    spent_on_stock = shares_to_buy * stock['Price']
                    
                    if total_spent + spent_on_stock <= money:
                        total_spent += spent_on_stock  # Update total spent
                        if shares_to_buy > 0:
                            print(f"Buy {shares_to_buy} shares of {stock['Stock']} for ${spent_on_stock:.2f}")
                            f.write(f"Swing,{stock['Stock']},{stock['Price']},{shares_to_buy},{spent_on_stock}\n")
                swing_ran = True

            if not swing_ran or (money - total_spent > 0):  # If swing stocks aren't enough or money is left
                dividend_money = money - total_spent if not swing_ran else dividend_money
                print(f"\n\nBuying Dividend Stocks with ${dividend_money:.2f}\n")
                
                # Process dividend stocks
                print(f"\n\nBuying Dividend Stocks with ${dividend_money:.2f}\n")
                stocks_to_buy = dividend_stocks[:top_n] if top_n else dividend_stocks
                for stock in stocks_to_buy:
                    weight = stock['Score'] / total_dividend_score
                    amount_to_invest = dividend_money * weight
                    shares_to_buy = max(1, int(amount_to_invest // stock['Price']))  # Ensure it's a multiple of stock price
                    spent_on_stock = shares_to_buy * stock['Price']
                    
                    if total_spent + spent_on_stock <= money:
                        total_spent += spent_on_stock  # Update total spent
                        if shares_to_buy > 0:
                            print(f"Buy {shares_to_buy} shares of {stock['Stock']} for ${spent_on_stock:.2f}")
                            f.write(f"Dividend,{stock['Stock']},{stock['Price']},{shares_to_buy},{spent_on_stock}\n")
                print(f"Total spent: ${total_spent:.2f}")

# Example usage
action = input("Do you want to 'buy' or 'sell'? ").strip().lower()

if action == 'buy':
    money = int(input("\nHow much money do you want to spend: "))
    calculate_stocks(money, total_spent, swing_stocks, dividend_stocks, total_swing_score, total_dividend_score, top_n, action='buy')
elif action == 'sell':
    calculate_sell_swing_stocks()
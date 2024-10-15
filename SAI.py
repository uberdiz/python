import pandas as pd
from sklearn.model_selection import train_test_split

# Load CSV into pandas dataframe
df = pd.read_csv("stock_data.csv")

# View the first few rows of the data
print(df.head())
# Selecting 'Close' as our target variable (what we want to predict)
df = df[['Date', 'Close']]
# Creating a new column for the next day's close price (target variable)
df['Target'] = df['Close'].shift(-1)

# Dropping the last row as it will have NaN in 'Target' column
df.dropna(inplace=True)

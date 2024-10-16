import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
import joblib

# Load the stock data CSV
df = pd.read_csv("stock_data.csv")

# Ensure 'Date' is parsed as a datetime object
df['Date'] = pd.to_datetime(df['Date'])

# Set 'Date' as the index of the DataFrame
df.set_index('Date', inplace=True)

# Define the features (X) and the target (y)
# Using 'Close' as the feature and target (predict next day 'Close')
X = df[['Close']]
y = df['Close'].shift(-1)  # Shift by one to predict the next day's closing price

# Drop NaN values resulting from the shift
X = X[:-1]
y = y[:-1]

# Split the data into training and testing sets (with shuffle=False to maintain date order)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False, random_state=42)

# Train the Linear Regression model
model = LinearRegression()
model.fit(X_train, y_train)

# Predict the test data
y_pred = model.predict(X_test)

# Save the trained model to a file
joblib.dump(model, 'stock_predictor.pkl')

# Plot the actual vs predicted prices
plt.figure(figsize=(10,6))
plt.plot(y_test.index, y_test, label="Actual Price", color='b')
plt.plot(y_test.index, y_pred, label="Predicted Price", color='r')
# Set the title and labels
plt.title("Stock Price Prediction (Linear Regression)")
plt.xlabel("Date")
plt.ylabel("Price")
# Format the x-axis to display dates in "YYYY-MM-DD" format
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
plt.gcf().autofmt_xdate()
plt.legend()
plt.show()

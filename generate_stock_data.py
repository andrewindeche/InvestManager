import json
from datetime import datetime

# Simulated stock data (you can modify these as needed)
stock_data = {
    'AAPL': 175.50,
    'GOOGL': 2800.10,
    'MSFT': 299.50,
    'TSLA': 702.50,
    'AMZN': 3342.88,
    'IBM': 217.16
}

# Get today's date in YYYY-MM-DD format
today_date = datetime.now().strftime('%Y-%m-%d')

# Prepare data for JSON file
data = {
    'date': today_date,
    'stocks': stock_data
}

# Write to JSON file
with open('stock_prices.json', 'w') as f:
    json.dump(data, f, indent=4)

print('Stock data JSON file has been created.')

import os
import json
from decimal import Decimal
import requests
from dotenv import load_dotenv
from requests.exceptions import HTTPError, ConnectionError, Timeout

load_dotenv()

# Load environment variables
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
ALPHA_VANTAGE_BASE_URL = os.getenv('ALPHA_VANTAGE_BASE_URL')
JSON_FILE_PATH = os.getenv('JSON_FILE_PATH', 'stock_prices.json')

def fetch_market_data(symbol):
    """
    Fetch real-time or simulated market data for a given symbol.
    """
    base_url = 'https://www.alphavantage.co/query'
    params = { 
        'apikey': ALPHA_VANTAGE_API_KEY,
        'function': 'GLOBAL_QUOTE',
        'symbol': symbol
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status() 
        data = response.json()
        
        if 'Global Quote' in data and '05. price' in data['Global Quote']:
            return {'price': float(data['Global Quote']['05. price'])}
        
    except (HTTPError, ConnectionError, Timeout) as e:
        print(f"Alpha Vantage error: {e}")
    try:
        with open(JSON_FILE_PATH, 'r',encoding='utf-8') as file:
            market_data = json.load(file)
            stocks = market_data.get('stocks', {})
            if symbol in stocks:
                return {'price': stocks[symbol]}
            else:
                return {'error': 'Price data not found in JSON file'}
    except FileNotFoundError:
        return {'error': 'JSON file not found'}
    except json.JSONDecodeError:
        return {'error': 'Error decoding JSON file'}

def calculate_investment_value(amount, price_per_unit):
    """
    Calculate the value of an investment.
    """
    return Decimal(amount) * Decimal(price_per_unit)

def simulate_transaction(account, amount, transaction_type, price_per_unit):
    """
    Simulates a buy or sell transaction, updates account and holdings.
    """
    account.balance = Decimal(account.balance)
    new_holding_value = calculate_investment_value(Decimal(amount), Decimal(price_per_unit))
    
    if transaction_type == 'buy':
        if account.balance < new_holding_value:
            raise ValueError("Insufficient funds to complete the purchase.")
        account.balance -= new_holding_value  
    elif transaction_type == 'sell':
        account.balance += new_holding_value
    else:
        raise ValueError("Invalid transaction type")
    
    account.save()
    return new_holding_value

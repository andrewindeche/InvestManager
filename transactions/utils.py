import os
import requests
from decimal import Decimal
from dotenv import load_dotenv

load_dotenv()

ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
ALPHA_VANTAGE_BASE_URL = os.getenv('ALPHA_VANTAGE_BASE_URL')

def fetch_market_data(symbol):
    """
    Fetch real-time or simulated market data for a given symbol.
    """
    params = {
        'function': 'TIME_SERIES_INTRADAY',
        'symbol': symbol,
        'interval': '5min',
        'apikey': ALPHA_VANTAGE_API_KEY
    }
    response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        return {'error': 'Failed to fetch market data'}

def calculate_investment_value(amount, price_per_unit):
    """
    Calculate the value of an investment.
    """
    return Decimal(amount) * Decimal(price_per_unit)

def simulate_transaction(account,amount, transaction_type, price_per_unit):
    """
    Simulates a buy or sell transaction, updates account and holdings.
    """
    new_holding_value = calculate_investment_value(amount, price_per_unit)
    
    if transaction_type == 'buy':
        if account.balance < new_holding_value:
            raise ValueError("Insufficient funds to complete the purchase.")
        account.balance -= new_holding_value
    elif transaction_type == 'sell':
        account.balance += new_holding_value
    else:
        raise ValueError("Invalid transaction type")
    
    return new_holding_value

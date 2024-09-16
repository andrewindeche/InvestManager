import os
from decimal import Decimal
import requests
from dotenv import load_dotenv

load_dotenv()

ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
ALPHA_VANTAGE_BASE_URL = os.getenv('ALPHA_VANTAGE_BASE_URL')

def fetch_market_data(symbol):
    """
    Fetch real-time or simulated market data for a given symbol.
    """
    api_key = 'ALPHA_VANTAGE_API_KEY'
    url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={api_key}'
    response = requests.get(url)
    data = response.json()
    
    if 'Global Quote' in data and '05. price' in data['Global Quote']:
        return {'price': float(data['Global Quote']['05. price'])}
    else:
        return {'error': 'Price data not found'}

def calculate_investment_value(amount, price_per_unit):
    """
    Calculate the value of an investment.
    """
    return Decimal(amount) * Decimal(price_per_unit)

def simulate_transaction(account,amount, transaction_type, price_per_unit):
    """
    Simulates a buy or sell transaction, updates account and holdings.
    """
    print(f"Account balance: {account.balance}")
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

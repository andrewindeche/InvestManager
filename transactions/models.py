from django.db import models
from accounts.models import User, Account
from django.utils import timezone
from .utils import fetch_market_data

class SimulatedInvestment(models.Model):
    """
    Model representing a simulation of the investment.
    """
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='simulated_investments')
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=10) 
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    units = models.DecimalField(max_digits=10, decimal_places=2)  
    transaction_type = models.CharField(max_length=10, choices=[('buy', 'Buy'), ('sell', 'Sell')])
    transaction_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        """
        Metaclass for the Investment renaming.
        """
        verbose_name = "Investment"  
        verbose_name_plural = "Investments" 

    def __str__(self):
        return f"{self.name} ({self.symbol}) - {self.units} units"
    
    def update_price(self):
        """
        Fetches real-time price from Alpha Vantage and updates the price_per_unit field.
        """
        market_data = fetch_market_data(self.symbol)
        if 'error' in market_data:
            raise ValueError(market_data['error'])
        
        try:
            price_per_unit = float(market_data['Time Series (5min)']['2024-09-10 10:00:00']['1. open'])
            self.price_per_unit = price_per_unit
            self.save()
        except (KeyError, ValueError) as exc:
            raise ValueError('Error fetching or parsing market data.') from exc
    
class Transaction(models.Model):
    """
    Model representing a transaction for buying or selling investments.
    """
    user = models.ForeignKey(User, related_name='transactions', on_delete=models.CASCADE)
    account = models.ForeignKey(Account, default=0, on_delete=models.CASCADE, related_name='transactions')
    investment = models.ForeignKey(SimulatedInvestment, null=True, blank=True, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    transaction_date = models.DateTimeField(default=timezone.now)
    transaction_type = models.CharField(max_length=10, default='buy', choices=[('buy', 'Buy'), ('sell', 'Sell')])

    def __str__(self):
        return f"{self.user.username} - {self.amount} ({self.transaction_type})"
    
    @property
    def price_per_unit(self):
        """
        Fetches and returns the price per unit of the investment at the time of transaction.
        """
        return self.investment.price_per_unit

    @property
    def units(self):
        """
        Returns the number of units involved in the transaction.
        """
        return self.amount / self.price_per_unit
    
class Holding(models.Model):
    """
    Model representing a holding within an account.
    """
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='holdings')
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    cost_basis = models.DecimalField(max_digits=10, decimal_places=2)
    current_value = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.account.name} - Holding with {self.quantity} units"
    
class InterestReturn(models.Model):
    """
    Model representing interest or returns for an investment.
    """
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='interest_returns')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.account.name} - {self.amount}"

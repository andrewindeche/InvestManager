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
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    units = models.DecimalField(max_digits=10, decimal_places=2)  
    transaction_type = models.CharField(max_length=10, choices=[('buy', 'Buy'), ('sell', 'Sell')])
    transaction_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        """
        Metaclass for the Investment renaming.
        """
        verbose_name = "Investment"  
        verbose_name_plural = "Investments" 

    def save(self, *args, **kwargs):
        """
        Fetch market data for the symbol from Alpha Vantage
        """
        market_data = fetch_market_data(self.symbol)
        
        if 'error' in market_data:
            raise ValueError(f"Error fetching market data for symbol {self.symbol}")

        self.price_per_unit = market_data['price'] 
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.symbol}) - {self.units} units"
    
    @property
    def total_value(self):
        """
        Function to dynamically calculate total value
        """
        return self.price_per_unit * self.units
    
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

from django.db import models
from accounts.models import User,Account
from django.utils import timezone

# Create your models here.

class Investment(models.Model):
    """
    Model representing an investment type.
    """
    STOCK = 'stock'
    BOND = 'bond'
    MUTUAL_FUND = 'mutual_fund'
    ETF = 'etf'
    MONEY_MARKET = 'money_market'

    INVESTMENT_CHOICES = [
        (STOCK, 'Stock'),
        (BOND, 'Bond'),
        (MUTUAL_FUND, 'Mutual Fund'),
        (ETF, 'ETF'),
    ]

    name = models.CharField(max_length=255)
    investment_type = models.CharField(max_length=20, choices=INVESTMENT_CHOICES)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return self.name
    
class Transaction(models.Model):
    """
    Model representing a transaction for buying or selling investments.
    """
    user = models.ForeignKey(User, related_name='transactions', on_delete=models.CASCADE)
    investment = models.ForeignKey(Investment, on_delete=models.CASCADE, default=1)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_date = models.DateTimeField(default=timezone.now)
    transaction_type = models.CharField(max_length=10, default='none', choices=[('buy', 'Buy'), ('sell', 'Sell')])

    def __str__(self):
        return f"{self.user.username} - {self.amount}"
    
class Holding(models.Model):
    """
    Model representing a holding within an account.
    """
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='holdings')
    investment = models.ForeignKey(Investment, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    cost_basis = models.DecimalField(max_digits=10, decimal_places=2)
    current_value = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.account.name} - {self.investment.name}"
    
class InterestReturn(models.Model):
    """
    Model representing interest or returns for an investment.
    """
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='interest_returns')
    investment = models.ForeignKey(Investment, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.account.name} - {self.investment.name} - {self.amount}"

from django.db import models
from accounts.models import User


# Create your models here.
class Transaction(models.Model):
    user = models.ForeignKey(User, related_name='transactions', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField()

    def __str__(self):
        return f"{self.user.username} - {self.amount}"
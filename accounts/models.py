from django.db import models

# Create your models here.

class User(models.Model):
    username = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    total_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return self.username

class Account(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    users = models.ManyToManyField(User, related_name='investor_accounts')

    def __str__(self):
        return self.name
    
class AccountPermissions(models.Model):
    VIEW_ONLY = 'view'
    FULL_ACCESS = 'full'
    POST_ONLY = 'post'

    PERMISSION_CHOICES = [
        (VIEW_ONLY, 'View Only'),
        (FULL_ACCESS, 'Full Access'),
        (POST_ONLY, 'Post Only'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    permission = models.CharField(max_length=10, choices=PERMISSION_CHOICES, default=VIEW_ONLY)

    class Meta:
        unique_together = ('user', 'account')

    def __str__(self):
        return f"{self.user.username} - {self.account.name} ({self.get_permission_display()})"

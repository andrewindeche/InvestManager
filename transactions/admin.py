from django.contrib import admin
from .models import Transaction,Investment
from django.contrib.auth.admin import UserAdmin

# Register your models here.
@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    """
    Admin interface for managing investments.

    This class defines how the Investment model should be presented in the Django admin interface.
    It allows administrators to view, edit, and manage investment records.
    """

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """
    Admin interface for managing transactions.

    This class defines how the Transaction model should be presented in the Django admin interface.
    It allows administrators to view, edit, and manage transaction records, including associating 
    transactions with users and investments.
    list_display = ('name', 'investment_type', 'interest_rate', 'tax_rate')
    """
    list_display = ('user', 'investment', 'amount', 'transaction_date', 'transaction_type')

from django.contrib import admin
from .models import Transaction,SimulatedInvestment
from django.contrib.auth.admin import UserAdmin

# Register your models here.
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """
    Admin interface for managing transactions.

    This class defines how the Transaction model should be presented in the Django admin interface.
    It allows administrators to view, edit, and manage transaction records, including associating 
    transactions with users and investments.
    """
    list_display = ('user','amount', 'transaction_date', 'transaction_type')
    search_fields = ('user__username', 'transaction_type')  
    list_filter = ('transaction_type', 'transaction_date') 
    
@admin.register(SimulatedInvestment)
class SimulatedInvestmentAdmin(admin.ModelAdmin):
    """
    Admin interface for managing simulated investments.
    """
    list_display = ('account', 'name', 'symbol', 'price_per_unit', 'units', 'transaction_type', 'transaction_date')
    search_fields = ('name', 'symbol')
    list_filter = ('transaction_type', 'transaction_date')

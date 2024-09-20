from django.contrib import admin
from accounts.models import AccountPermissions
from .models import SimulatedInvestment, Transaction
from django.utils.html import format_html

class SimulatedInvestmentAdmin(admin.ModelAdmin):
    """
    Admin interface for managing simulated investments in KES.
    """
    list_display = ('users_list', 'account', 'name', 'symbol', 'price_per_unit', 'units', 'total_value_kes', 'transaction_date') 
    list_filter = (('transaction_date', admin.DateFieldListFilter),)
    search_fields = ('account__users__username', 'account__name', 'name')

    def get_queryset(self, request):
        """
        Filter and display investments related to accounts accessible to the user.
        """
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        account_ids = AccountPermissions.objects.filter(user=request.user).values_list('account_id', flat=True)
        return qs.filter(account_id__in=account_ids)

    def total_value_kes(self, obj):
        """
        Calculate the total value of the current investment in Kenyan Shillings (KES).
        """
        total_value = obj.price_per_unit * obj.units
        kes_value = total_value * 140  
        return format_html(f"KES {kes_value:,.2f}")

    total_value_kes.short_description = 'Total Value (KES)'

    def users_list(self, obj):
        """
        List all users associated with the account.
        """
        users = obj.account.users.all()
        user_names = ", ".join([user.username for user in users])
        return format_html(user_names)

    users_list.short_description = "Users"

admin.site.register(SimulatedInvestment, SimulatedInvestmentAdmin)

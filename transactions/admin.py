from django.contrib import admin
from .models import SimulatedInvestment
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

class SimulatedInvestmentAdmin(admin.ModelAdmin):
    """
    Admin interface for managing simulated investments in kes.
    """
    list_display = ('account', 'name', 'symbol', 'price_per_unit', 'units', 'total_value_kes', 'user_total_investments_kes')
    list_filter = (('transaction_date', admin.DateFieldListFilter),)
    
    def total_value_kes(self, obj):
        """
        Calculate the total value of the current investment in Kenyan Shillings (KES).
        """
        total_value = obj.price_per_unit * obj.units
        kes_value = total_value * 140 
        return format_html(f"KES {kes_value:,.2f}")

    total_value_kes.short_description = 'Total Value (KES)'

    def user_total_investments_kes(self, obj):
        """
        Calculate the total value of all investments by the user, in KES.
        """
        user_investments = SimulatedInvestment.objects.filter(account=obj.account)
        total_value = sum([investment.price_per_unit * investment.units for investment in user_investments])
        kes_total_value = total_value * 140 
        return format_html(f"KES {kes_total_value:,.2f}")
    
    user_total_investments_kes.short_description = "User's Total Investments (KES)"
    
admin.site.register(SimulatedInvestment, SimulatedInvestmentAdmin)

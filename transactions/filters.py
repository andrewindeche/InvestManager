import django_filters
from .models import Transaction

class TransactionFilter(django_filters.FilterSet):
    """
    Class for filer logic based on dates
    """
    start_date = django_filters.DateFilter(field_name='transaction_date', lookup_expr='gte')
    end_date = django_filters.DateFilter(field_name='transaction_date', lookup_expr='lte')

    class Meta:
        """
        Filter logic constraints
        """
        model = Transaction
        fields = ['start_date', 'end_date']
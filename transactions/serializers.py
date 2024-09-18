from decimal import Decimal
from rest_framework import serializers
from transactions.models import Transaction, InterestReturn,SimulatedInvestment

class InvestmentSerializer(serializers.ModelSerializer):
    """
    Serializer for the Investment model.
    """
    class Meta:
        """
        Metaclass for the Simulated investments contraints.
        """
        model = SimulatedInvestment
        fields = (['account', 'name',
                   'symbol', 'price_per_unit', 
                   'units', 'transaction_type', 
                   'transaction_date']
                  )

class TransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for the Transaction model.
    """
    price_per_unit = serializers.ReadOnlyField()
    units = serializers.ReadOnlyField(source='units')

    class Meta:
        """
        Metaclass for the Simulated Transaction contraints.
        """
        model = Transaction
        fields = (['user', 'account',
                   'investment', 'amount', 
                   'transaction_date', 
                   'transaction_type', 
                   'price_per_unit', 'units']
                  )
        def validate_amount(self, value):
            """
            Method to validate data type of amount
            """
            if not isinstance(value, (int, float, Decimal)):
                raise serializers.ValidationError("Invalid amount format")
            return value
class InterestReturnSerializer(serializers.ModelSerializer):
    """
    Serializer for the InterestReturn model.
    """
    class Meta:
        """
        Metaclass for the InterestReturn contraints.
        """
        model = InterestReturn
        fields = '__all__'
        
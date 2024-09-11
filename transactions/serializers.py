from rest_framework import serializers
from transactions.models import Transaction, Investment, Holding, InterestReturn
from accounts.serializers import UserSerializer

class TransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for the Transaction model.
    """
    user = UserSerializer(read_only=True)

    class Meta:
        """
        Metaclass for the Transaction contraints.
        """
        model = Transaction
        fields = ['id', 'user', 'amount', 'date']
        
class InvestmentSerializer(serializers.ModelSerializer):
    """
    Serializer for the Investment model.
    """
    class Meta:
        """
        Metaclass for the Investment contraints.
        """
        model = Investment
        fields = '__all__'
        
class HoldingSerializer(serializers.ModelSerializer):
    """
    Serializer for the Holding model.
    """
    class Meta:
        """
        Metaclass for the Holding contraints.
        """
        model = Holding
        fields = '__all__'
        
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
        
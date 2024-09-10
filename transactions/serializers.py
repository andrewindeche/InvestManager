from rest_framework import serializers
from django.contrib.auth.models import Transaction

class TransactionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Transaction
        fields = ['id', 'user', 'amount', 'date']
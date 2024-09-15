from accounts.models import AccountPermissions,Account
from .models import Transaction,InterestReturn,SimulatedInvestment
from decimal import Decimal
from django.http import JsonResponse
from rest_framework.response import Response
from django.db.models import Sum
from rest_framework import viewsets 
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView 
from .serializers import (
    TransactionSerializer,
    InterestReturnSerializer,
    InvestmentSerializer
    )
from django.shortcuts import get_object_or_404
from .utils import fetch_market_data, simulate_transaction

# Create your views here.
class TransactionViewSet(viewsets.ModelViewSet):
    """
    A unified viewset for handling both account and investment transactions.

    - Requires user authentication.
    - Handles permissions for both account and investment transactions.
    """
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Fetches transactions based on the user's permissions for the account or investment.
        - If the user has 'VIEW_ONLY' permission, they cannot view any transactions.
        - If the user has 'POST_ONLY' permission, they can view only their own transactions.
        - If the user has 'FULL_ACCESS', they can view all transactions.
        """
        user = self.request.user
        account_id = self.kwargs.get('account_pk')
        account = get_object_or_404(Account, pk=account_id)
        permission = get_object_or_404(AccountPermissions, user=user, account=account)

        if permission.permission == AccountPermissions.VIEW_ONLY:
            return Transaction.objects.none()  
        elif permission.permission == AccountPermissions.POST_ONLY:
            return Transaction.objects.filter(user=user, account=account)  
        return Transaction.objects.filter(account=account)

    def perform_create(self, serializer):
        """
        Creates a transaction if the user has sufficient permissions.
        Only users with 'FULL_ACCESS' or 'POST_ONLY' can create a transaction.
        """
        investment = serializer.validated_data['investment']
        investment.update_price()
        super().perform_create(serializer)


class UserTransactionsAdminView(APIView):
    """
    An API view for admin users to retrieve transactions and the total balance for a specific user.

    - Allows filtering transactions by a date range using 'start_date' and 'end_date' query parameters.

    Methods:
        - get(): Fetches and returns the transactions for a specific user within an optional date range.
    """
    def get(self, request, user_id):
        """
        Retrieves transactions for a specific user, optionally filtering by date range.

        - If 'start_date' and 'end_date' are provided in the query parameters, transactions within that range are returned.
        - Calculates the total balance of the retrieved transactions.
        """
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        transactions = Transaction.objects.filter(user_id=user_id)

        if start_date and end_date:
            transactions = transactions.filter(date__range=[start_date, end_date])

        total_balance = transactions.aggregate(Sum('amount'))['amount__sum']

        data = {
            'transactions': TransactionSerializer(transactions, many=True).data,
            'total_balance': total_balance,
        }

        return Response(data)
    
class InterestReturnViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing InterestReturn instances.
    """
    serializer_class = InterestReturnSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        This view should return a list of all interest returns
        for the currently authenticated user.
        """
        user = self.request.user
        return InterestReturn.objects.filter(account__users=user)

class SimulatedInvestmentTransactionView(APIView):
    """
    API view to simulate buying and selling investments based on market data.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, account_pk):
        """
        Simulates a transaction (buy/sell) for the given investment.
        """
        account = get_object_or_404(Account, pk=account_pk, users=request.user)
        account.balance = Decimal('20000.00')
        account.save()
        
        transaction_type = request.data.get('transaction_type')
        amount = request.data.get('amount')
        symbol = request.data.get('symbol')

        amount = Decimal(amount)
        market_data = fetch_market_data(symbol)

        if 'error' in market_data:
            return Response({'error': market_data['error']}, status=400)

        price_per_unit = market_data['price']
        price_per_unit = Decimal(price_per_unit)
        
        if not price_per_unit:
            return Response({'error': 'Open price data not available'}, status=400)

        try:
            investment_value = simulate_transaction(account, amount, transaction_type, price_per_unit)
        except ValueError as e:
            return Response({'error': str(e)}, status=400)
        
        investment, created = SimulatedInvestment.objects.get_or_create(
            account=account,
            symbol=symbol,
            defaults={'name': symbol, 'units': amount / price_per_unit, 'transaction_type': transaction_type}
        )
        if not created:
            investment.units += amount / price_per_unit if transaction_type == 'buy' else -amount / price_per_unit
            investment.save()

        account.save()

        return Response({
            'message': f'Successfully {transaction_type} transaction of {amount} units of {investment.name}',
            'investment_value': investment_value
        }, status=200)
        
class InvestmentViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing SimulatedInvestment instances.
    """
    serializer_class = InvestmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return Simulated Investment objects from a query
        """
        user = self.request.user
        if user.is_staff:
            return SimulatedInvestment.objects.all()
        else:
            return SimulatedInvestment.objects.filter(account__users=user)
        
        
class PerformanceView(APIView):
    """
    View to handle fetching stock performance data from Alpha Vantage API.
    
    This view retrieves real-time or simulated intraday market data for a given stock symbol
    using the Alpha Vantage API. The symbol is passed as a query parameter in the request.
     """
    def get(self, request, *args, **kwargs):
        """
         Handle GET requests to fetch stock market data from the Alpha Vantage API.
        """
        symbol = request.GET.get('symbol', 'AAPL')
        
        data = fetch_market_data(symbol)

        if 'error' in data:
            return JsonResponse({"error": data['error']}, status=500)

        return JsonResponse(data)
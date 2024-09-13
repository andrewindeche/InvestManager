from accounts.models import AccountPermissions,Account
from .models import Transaction, Investment,InterestReturn,Holding
from django.http import JsonResponse
from rest_framework.response import Response
from django.db.models import Sum
from rest_framework import status,viewsets 
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView 
from .serializers import (
    TransactionSerializer,
    InterestReturnSerializer,
    HoldingSerializer,
    InvestmentSerializer
    )
from django.shortcuts import get_object_or_404
from .utils import fetch_market_data, simulate_transaction

# Create your views here.
class TransactionViewSet(viewsets.ModelViewSet):
    """
     A viewset for handling transaction-related operations for a specific account.

    - Requires the user to be authenticated.
    - Manages permissions to view or create transactions based on the user's permissions for the account.
    """
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Fetches transactions based on the user's permissions for the account.

        - If the user has 'VIEW_ONLY' permission, they cannot view any transactions.
        - If the user has 'POST_ONLY' permission, they can view only their own transactions.
        - If the user has 'FULL_ACCESS', they can view all transactions related to the account.
        """
        
        user = self.request.user
        account_id = self.kwargs.get('account_pk')
        account = get_object_or_404(Account, pk=account_id)
        permission = get_object_or_404(AccountPermissions, user=user, account=account)

        if permission.permission == AccountPermissions.VIEW_ONLY:
            return Transaction.objects.none()  
        elif permission.permission == AccountPermissions.POST_ONLY:
            return Transaction.objects.filter(user=user)  
        return Transaction.objects.all()  

    def create(self, request, *args, **kwargs):
        """
        Handles the creation of a new transaction if the user has sufficient permissions.

        - Only users with 'FULL_ACCESS' or 'POST_ONLY' permissions can create a new transaction.
        - If the user lacks permission, returns a 403 Forbidden response.
        """
        user = request.user
        account_id = self.kwargs.get('account_pk')
        account = get_object_or_404(Account, pk=account_id)
        permission = get_object_or_404(AccountPermissions, user=user, account=account)
      

        if permission.permission != AccountPermissions.FULL_ACCESS and permission.permission != AccountPermissions.POST_ONLY:
            return Response({'detail': 'Permission denied to post transactions.'}, status=status.HTTP_403_FORBIDDEN)

        return super().create(request, *args, **kwargs)
    
class InvestmentTransactionViewSet(viewsets.ModelViewSet):
    """
     A viewset for carrying out a simulated transaction based on amounts and price .
    - Requires the user to be authenticated.
    """
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user = request.user
        account_id = kwargs.get('account_pk')
        account = get_object_or_404(Account, pk=account_id, users=user)

        investment_id = request.data.get('investment')
        investment = get_object_or_404(Investment, pk=investment_id)

        amount = Decimal(request.data.get('amount'))
        if account.balance < amount:
            return Response({'error': 'Insufficient balance'}, status=status.HTTP_400_BAD_REQUEST)

        transaction = Transaction.objects.create(
            user=user, account=account, investment=investment, amount=amount,
            transaction_type='buy'
        )

        account.balance -= amount
        account.save()

        holding, created = Holding.objects.get_or_create(account=account, investment=investment)
        holding.quantity += amount / investment.price 
        holding.current_value += amount
        holding.save()

        return Response(TransactionSerializer(transaction).data, status=status.HTTP_201_CREATED)

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
    
class HoldingViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Holding instances.
    """
    serializer_class = HoldingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        This view should return a list of all holdings
        for the currently authenticated user.
        """
        user = self.request.user
        return Holding.objects.filter(account__users=user)
    
class InvestmentViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Investment instances.
    """
    serializer_class = InvestmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        This view should return a list of all investments.
        """
        return Investment.objects.all()
    
class SimulatedInvestmentTransactionView(APIView):
    """
    API view to simulate buying and selling investments based on market data.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, account_pk, investment_id):
        """
        Simulates a transaction (buy/sell) for the given investment.
        """
        account = get_object_or_404(Account, pk=account_pk, users=request.user)
        investment = get_object_or_404(Investment, pk=investment_id)

        transaction_type = request.data.get('transaction_type')
        amount = request.data.get('amount')
        symbol = request.data.get('symbol')

        market_data = fetch_market_data(symbol)

        if 'error' in market_data:
            return Response({'error': market_data['error']}, status=400)

        price_per_unit = market_data['Time Series (5min)']['2024-09-10 10:00:00']['1. open']

        try:
            investment_value = simulate_transaction(account, investment, amount, transaction_type, price_per_unit)
        except ValueError as e:
            return Response({'error': str(e)}, status=400)

        account.save()

        return Response({
            'message': f'Successfully {transaction_type}ed {amount} units of {investment.name}',
            'investment_value': investment_value
        }, status=200)
        
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
from decimal import Decimal
from django.shortcuts import get_object_or_404
from accounts.models import AccountPermissions,Account,User
from .models import Transaction,SimulatedInvestment
from django.http import JsonResponse
from django.utils.dateparse import parse_date
from rest_framework.response import Response
from django.db import IntegrityError
from rest_framework import viewsets 
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from rest_framework.views import APIView 
from .serializers import (
    TransactionSerializer,
    InvestmentSerializer
    )
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
        
class TransactionListView(APIView):
    """
    API view to list transactions for the authenticated user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, account_pk):
        """
        Retrieves all transactions for the given account and user.
        """
        account = get_object_or_404(Account, pk=account_pk)
        
        permission = AccountPermissions.objects.filter(user=request.user, account=account).first()
        if permission is None or permission.permission == AccountPermissions.POST_ONLY:
            return Response({'error': 'You do not have permission to view transactions for this account'}, status=403)

        transactions = Transaction.objects.filter(account=account, user=request.user)
        serializer = TransactionSerializer(transactions, many=True) 
        return Response(serializer.data, status=200)


class UserTransactionsAdminView(APIView):
    """
    An API view for admin users to retrieve transactions and the total balance for a specific user.

    - Allows filtering transactions by a date range using 'start_date' and 'end_date' query parameters.

    Methods:
        - get(): Fetches and returns the transactions for a specific user within an optional date range.
    """
    permission_classes = [IsAdminUser]
    
    def get(self, request, username):
        """
        Retrieves transactions for a specific user, optionally filtering by date range.

        - If 'start_date' and 'end_date' are provided in the query parameters, transactions within that range are returned.
        - Calculates the total balance of the retrieved transactions.
        """
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        usd_to_kes_rate = Decimal('140.00')

        user = get_object_or_404(User, username=username)

        transactions = Transaction.objects.filter(user=user)

        if start_date and end_date:
            transactions = transactions.filter(transaction_date__range=[start_date, end_date])
        
        investments = SimulatedInvestment.objects.filter(account__users=user)

        total_investments =  sum([Decimal(inv.total_value) for inv in investments])
        total_investments_in_kes = sum([Decimal(inv.total_value) for inv in investments]) * usd_to_kes_rate

        investment_data = []
        for investment in investments:
            total_value_kes = Decimal(investment.total_value) * usd_to_kes_rate
            investment_data.append({
                'user': user.username,
                'account': investment.account.name,
                'name': investment.name,
                'symbol': investment.symbol,
                'units': investment.units,
                'price_per_unit': investment.price_per_unit,
                'total_value': investment.total_value,
                'total_value_kes': total_value_kes,
             })
        
        data = {
            'total_investments': total_investments,
            'total_investments_in_kes': total_investments_in_kes,
            'investments': investment_data,
        }

        return Response(data)

class UserTransactionsView(APIView):
    """
    API view for non-admin users to retrieve their transactions, enforcing POST_ONLY permissions.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, account_pk):
        """
        Retrieves transactions for the current user and checks permissions for the account.
        Users with POST_ONLY permission cannot view transactions.
        """
        account = get_object_or_404(Account, pk=account_pk, users=request.user)
        permission = AccountPermissions.objects.filter(user=request.user, account=account).first()

        if permission.permission == AccountPermissions.POST_ONLY:
            return Response({'error': 'You do not have permission to view transactions for this account.'}, status=403)

        transactions = Transaction.objects.filter(user=request.user, account=account)
        transaction_data = [
            {
                'amount': transaction.amount,
                'transaction_type': transaction.transaction_type,
                'date': transaction.transaction_date,
            }
            for transaction in transactions
        ]

        return Response({'transactions': transaction_data})

class SimulatedInvestmentTransactionView(APIView):
    """
    API view to simulate buying and selling investments based on market data.
    """
    permission_classes = [IsAuthenticated]
    def get_permissions(self):
        """
        Method for enforcing POST permissions
        """
        if self.request.method == 'POST':
            return [IsAuthenticated()] 
        return super().get_permissions()

    def post(self, request, account_pk):
        """
        Method that Simulates a transaction (buy/sell) for the given investment.
        """
        account = get_object_or_404(Account, pk=account_pk, users=request.user)
        account.balance = Decimal('20000.00')
        account.save()
        
        permission = AccountPermissions.objects.filter(user=request.user, account=account).first()
        if permission is None:
            return Response({'error': 'You do not have permission to access this account'}, status=403)

        if permission.permission == AccountPermissions.VIEW_ONLY:
            return Response({'error': 'You only have view permissions for this account'}, status=403)
        
        if permission.permission == AccountPermissions.POST_ONLY:
            if self.request.method != 'POST':
                return Response({'error': 'You can only post transactions'}, status=403)
        
        transaction_type = request.data.get('transaction_type')
        amount = request.data.get('amount')
        symbol = request.data.get('symbol')

        try:
            amount = Decimal(amount)
        except (ValueError, TypeError):
            return Response({'error': 'Invalid amount format'}, status=400)

        market_data = fetch_market_data(symbol)

        if 'error' in market_data:
            return Response({'error': market_data['error']}, status=400)

        price_per_unit = market_data.get('price')
        
        if price_per_unit is None:
            return Response({'error': 'Open price data not available'}, status=400)

        try:
            price_per_unit = Decimal(price_per_unit)
        except (ValueError, TypeError):
            return Response({'error': 'Price data is invalid'}, status=400)

        try:
            investment_value = simulate_transaction(account, amount, transaction_type, price_per_unit)
        except ValueError as e:
            return Response({'error': str(e)}, status=400)

        try:
            investment, created = SimulatedInvestment.objects.get_or_create(
                account=account,
                symbol=symbol,
                defaults={'name': symbol, 'units': amount / price_per_unit, 'transaction_type': transaction_type}
            )
            if not created:
                if transaction_type == 'buy':
                    investment.units += amount / price_per_unit
                elif transaction_type == 'sell':
                    investment.units -= amount / price_per_unit
                investment.save()

        except IntegrityError:
            return Response({'error': 'Duplicate investment entry detected'}, status=400)

        account.save()

        return Response({
            'message': f'Successfully {transaction_type} transaction of {amount} units of {investment.name}',
            'investment_value': investment_value
        }, status=200)

class InvestmentDateFilterView(APIView):
    """
    API view to filter investments by date.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get start and stop dates of transaction creation
        """
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if start_date and end_date:
            start_date = parse_date(start_date)
            end_date = parse_date(end_date)
            investments = SimulatedInvestment.objects.filter(created_at__range=[start_date, end_date])
        else:
            investments = SimulatedInvestment.objects.all()

        data = [{
            'account': investment.account.id,
            'name': investment.name,
            'symbol': investment.symbol,
            'price_per_unit': str(investment.price_per_unit),
            'units': str(investment.units),
            'created_at': investment.created_at
        } for investment in investments]

        return Response(data)
        
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
    def get(self, request):
        """
         Handle GET requests to fetch stock market data from the Alpha Vantage API.
        """
        symbol = request.GET.get('symbol', 'AAPL')
        
        data = fetch_market_data(symbol)

        if 'error' in data:
            return JsonResponse({"error": data['error']}, status=500)

        return JsonResponse(data)
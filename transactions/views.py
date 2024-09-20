from decimal import Decimal,InvalidOperation
from django.core.exceptions import PermissionDenied,ValidationError
from django.shortcuts import get_object_or_404

from django.http import JsonResponse
from django.utils.dateparse import parse_date

from rest_framework import viewsets
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import IsAuthenticated,IsAdminUser
from rest_framework.views import APIView
from rest_framework.response import Response

from accounts.models import AccountPermissions,Account,User
from .filters import TransactionFilter
from .models import Transaction,SimulatedInvestment
from .utils_permissions import process_transaction
from .serializers import (
    TransactionSerializer,
    InvestmentSerializer
    )
from .utils import fetch_market_data

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
        serializer.save(user=self.request.user)
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
            return Response(
                {'error': 'You do not have permission to view transactions for this account'
                 },
                status=403
                )

        transactions = Transaction.objects.filter(account=account, user=request.user)
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data, status=200)

class UserTransactionsAdminView(APIView):
    """
    An API view for admin users to retrieve transactions 
    and the total balance for a specific user.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = TransactionSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = TransactionFilter

    def get(self, request, username):
        """
        Retrieves transactions for a specific user, optionally filtering by date range.
        """
        user = get_object_or_404(User, username=username)
        transactions = Transaction.objects.filter(user=user)
        filterset = TransactionFilter(request.GET, queryset=transactions)
        if not filterset.is_valid():
            return Response(filterset.errors, status=400)
        
        transactions = filterset.qs
        serializer = self.serializer_class(transactions, many=True)

        usd_to_kes_rate = Decimal('140.00')
        investments = SimulatedInvestment.objects.filter(account__users=user)
        total_investments = sum([Decimal(inv.total_value) for inv in investments])
        total_investments_in_kes = total_investments * usd_to_kes_rate

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
            'transactions': serializer.data,
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
            return Response(
                {'error': 'You do not have permission to view transactions for this account.'
                 }, status=403)

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
        Method for enforcing POST permissions.
        """
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return super().get_permissions()

    def post(self, request, account_pk):
        """
        Method that simulates a transaction (buy/sell) for the given investment.
        """
        transaction_type = request.data.get('transaction_type')
        units = request.data.get('units')
        symbol = request.data.get('symbol')

        if transaction_type not in ['buy', 'sell']:
            return Response({'error': 'Invalid transaction type'}, status=400)

        if units is None:
            return Response({'error': 'Units are required'}, status=400)

        try:
            units = Decimal(units)
        except (InvalidOperation, ValueError):
            return Response({'error': 'Invalid units format'}, status=400)

        if not symbol:
            return Response({'error': 'Symbol is required'}, status=400)

        account = get_object_or_404(Account, pk=account_pk, users=request.user)

        # Use filter instead of get to handle multiple objects
        investments = SimulatedInvestment.objects.filter(account=account, symbol=symbol)

        if not investments.exists():
            return Response({'error': 'No investment found for the given symbol'}, status=404)

        total_investment_value = Decimal('0.00')
        usd_to_kes_rate = Decimal('140.00')

        for investment in investments:
            try:
                result = process_transaction(
                    user=request.user,
                    account_pk=account.pk,
                    transaction_type=transaction_type,
                    units=units,
                    symbol=symbol
                )
            except PermissionDenied as e:
                return Response({'error': str(e)}, status=403)
            except ValidationError as e:
                return Response({'error': str(e)}, status=400)
            except ValueError as e:
                return Response({'error': str(e)}, status=400)

            investment_value = result.get('investment_value')
            if investment_value:
                total_investment_value += investment_value

        investment_value_kes = total_investment_value * usd_to_kes_rate if total_investment_value else None

        return Response({
            'message': f'Successfully {transaction_type} {units} units of {symbol}',
            'total_investment_value': f'{total_investment_value:.2f} USD' if total_investment_value else None,
            'total_investment_value_kes': f'{investment_value_kes:.2f} KES' if investment_value_kes else None
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
            return SimulatedInvestment.objects.filter(
                account__users=user
            )
            
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
    
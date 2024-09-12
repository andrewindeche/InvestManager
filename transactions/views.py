from .models import Transaction, Investment,InterestReturn
from accounts.models import AccountPermissions,Account,Holding
from rest_framework.response import Response
from django.db.models import Sum
from rest_framework import status,viewsets 
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView 
from .serializers import TransactionSerializer,InterestReturnSerializer,HoldingSerializer,InvestmentSerializer
from django.shortcuts import get_object_or_404

# Create your views here.
class TransactionViewSet(viewsets.ModelViewSet):
    """
     A viewset for handling transaction-related operations for a specific account.

    - Requires the user to be authenticated.
    - Manages permissions to view or create transactions based on the user's permissions for the account.
    """

    Methods:
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
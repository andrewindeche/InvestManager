from django.shortcuts import render
from .models import Transaction
from accounts.models import AccountPermissions
from rest_framework import generics, permissions, viewsets
from rest_framework.permissions import IsAuthenticated
from accounts.serializers import AccountPermissionsSerializer
from rest_framework.views import APIView 
from .serializers import TransactionSerializer
from django.shortcuts import get_object_or_404

# Create your views here.
class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
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
        user = request.user
        account_id = self.kwargs.get('account_pk')
        account = get_object_or_404(Account, pk=account_id)
        permission = get_object_or_404(AccountPermissions, user=user, account=account)

        # Check permission before creating transactions
        if permission.permission != AccountPermissions.FULL_ACCESS and permission.permission != AccountPermissions.POST_ONLY:
            return Response({'detail': 'Permission denied to post transactions.'}, status=status.HTTP_403_FORBIDDEN)

        return super().create(request, *args, **kwargs)

class UserTransactionsAdminView(APIView):
    def get(self, request, user_id):
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
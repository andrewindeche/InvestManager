from django.shortcuts import render
from .models import AccountPermissions, Transaction
from .serializers import AccountPermissionsSerializer, TransactionSerializer
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

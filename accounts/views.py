from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import generics, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth.models import User
from accounts.models import Account, AccountPermissions
from .serializers import *

# Create your views here.
class RegisterView(generics.CreateAPIView):
    """
    A viewset for user creation.
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
      
    def create(self, request):
        """
        This view should create refresh and access tokens once a 
        user account is created
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)

class LoginView(generics.CreateAPIView):
    """
    A viewset for logging in authenticated users.
    """
    serializer_class = LoginSerializer

    def create(self, request):
        """
        This view should create refresh and access tokens once a 
        user is authenticated or an error status for authentication
        bugs.
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            tokens = serializer.get_tokens(user)
            return Response({
                'refresh': tokens['refresh'],
                'access': tokens['access'],
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
     
class AccountViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Account instances.
    """
    serializer_class = AccountSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        This view should return a list of all the accounts
        for the currently authenticated user.
        """
        user = self.request.user
        if user.is_staff:
            return Account.objects.all()
        return Account.objects.filter(users=user)
   
    def perform_create(self, serializer):
        """
        Allow users to create accounts with specific permissions.
        """
        account = serializer.save()
        account.users.add(self.request.user)
        permission = self.request.data.get('permission', AccountPermissions.VIEW_ONLY)
        AccountPermissions.objects.create(user=self.request.user, account=account, permission=permission)

class AccountPermissionsViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Account permissions.
    """
    serializer_class = AccountPermissionsSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """
        Return the list of permissions for the current user.
        """
        user = self.request.user
        if user.is_staff:
            return AccountPermissions.objects.all()
        return AccountPermissions.objects.filter(user=user)

    def get_serializer_class(self):
        """
        Return the appropriate serializer class based on the request method.
        """
        if self.request.method == 'PUT':
            return AccountPermissionsUpdateSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        """
        Allow only admin users to create permissions.
        """
        if not self.request.user.is_staff:
            raise PermissionDenied("You do not have permission to create permissions.")
        serializer.save()

    def perform_update(self, serializer):
        """
        Allow only admin users to update permissions.
        """
        if not self.request.user.is_staff:
            raise PermissionDenied("You do not have permission to update permissions.")
        serializer.save()

    def perform_destroy(self, instance):
        """
        Allow only admin users to delete permissions.
        """
        if not self.request.user.is_staff:
            raise PermissionDenied("You do not have permission to delete permissions.")
        instance.delete()
        
    def create(self, request, *args, **kwargs):
        """
        Handle the creation of a new AccountPermission with a success message.
        """
        if not self.request.user.is_staff:
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        response = super().create(request, *args, **kwargs)
        return Response({'detail': 'Permission created successfully.', 'data': response.data}, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """
        Handle the update of an AccountPermission with a success message.
        """
        if not self.request.user.is_staff:
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        response = super().update(request, *args, **kwargs)
        return Response({'detail': 'Permission updated successfully.', 'data': response.data}, status=status.HTTP_200_OK)

    def destroy(self,request, *args, **kwargs):
        """
        Handle the deletion of an AccountPermission with a success message.
        """
        if not self.request.user.is_staff:
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        
        super().destroy(request, *args, **kwargs)
        return Response({'detail': 'Permission deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)

class SelectAccountViewSet(viewsets.ViewSet):
    """
    A viewset for selecting the current account for the user.
    """
    permission_classes = [IsAuthenticated]

    def update(self, request, pk=None):
        """
        Update the current account for the authenticated user.
        """
        try:
            account = Account.objects.filter(pk=pk, users=request.user).first()
            if not account:
                raise Account.DoesNotExist
            
            request.user.current_account = account
            request.user.save()

            return Response({'status': 'account set'}, status=status.HTTP_200_OK)

        except Account.DoesNotExist:
            return Response({'error': 'Account not found or not accessible'}, 
                            status=status.HTTP_404_NOT_FOUND)     

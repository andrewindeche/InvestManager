from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.views import APIView 
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import generics, viewsets
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from accounts.models import Account, AccountPermissions
from transactions.models import Transaction
from .serializers import *

# Create your views here.
class RegisterView(generics.CreateAPIView):
    """
    A viewset for user creation.
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
      
    def create(self, request, *args, **kwargs):
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

    def create(self, request, *args, **kwargs):
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
        return Account.objects.all()

class AccountPermissionsViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Account permissions.
    """
    serializer_class = AccountPermissionsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        This view should return a list of all the accounts
        permissions for the currently authenticated users.
        """
        return AccountPermissions.objects.filter(user=self.request.user)

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
            account = Account.objects.get(pk=pk, users=request.user)
            request.user.current_account = account
            request.user.save()
            return Response({'status': 'account set'}, status=status.HTTP_200_OK)
        except Account.DoesNotExist:
            return Response({'error': 'Account not found or not accessible'}, status=status.HTTP_404_NOT_FOUND)
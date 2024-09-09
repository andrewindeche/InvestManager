from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import CreateAPIView, GenericAPIView
from django.contrib.auth.models import User
from .serializers import RegisterSerializer, LoginSerializer

# Create your views here.
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

class LoginView(generics.CreateAPIView):
    serializer_class = LoginSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            tokens = serializer.get_tokens(user)
            return Response({
                'refresh': tokens['refresh'],
                'access': tokens['access'],
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
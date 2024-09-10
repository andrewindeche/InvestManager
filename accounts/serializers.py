from rest_framework import serializers
from django.contrib.auth.models import User
from accounts.models import Account, AccountPermissions
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.tokens import RefreshToken

class LoginSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['username', 'password']

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                if not user.is_active:
                    raise serializers.ValidationError("This account is not active.")
                data['user'] = user
            else:
                raise serializers.ValidationError("Invalid username or password.")
        else:
            raise serializers.ValidationError("Must include both 'username' and 'password'.")
        
        return data

    def get_tokens(self, user):
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('username', 'email',  'password', 'confirm_password')

    def validate(self, data):
        if 'password' not in data or 'confirm_password' not in data:
            raise serializers.ValidationError("Password and Confirm Password are required")
        
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        
        username = data.get('username')
        email = data.get('email')

        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError("This username is already in use.")
        
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("This email address is already registered.")
        
        try:
            validate_password(data['password'])
        except Exception as e:
            raise serializers.ValidationError(str(e))

        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(**validated_data)
        return user
    
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'total_balance']
        
class AccountSerializer(serializers.ModelSerializer):
    users = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Account
        fields = ['id', 'name', 'description', 'users']
        
class AccountPermissionsSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    account = AccountSerializer(read_only=True)

    class Meta:
        model = AccountPermissions
        fields = ['id', 'user', 'account', 'permission']   
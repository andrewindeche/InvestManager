from rest_framework import serializers
from django.contrib.auth.models import User
from accounts.models import Account,Investor, AccountPermissions
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.tokens import RefreshToken

class LoginSerializer(serializers.ModelSerializer):
    """
    Serializer for User Login.
    """
    username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        """
        Metaclass for the User contraints.
        """
        model = User
        fields = ['username', 'password']

    def validate(self, data):
        """
        Validate a given user based on correct username and password.

        Args:
            user (Authenticated User): The user for whom the tokens are generated.
        """
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
        """
        Generate and return refresh and access tokens for a given user.

        Args:
            user (Any): The user for whom the tokens are generated.

        Returns:
            dict[str, str]: A dictionary containing the refresh and access tokens.
        """
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for User Registration.
    """
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        """
        Meta class for the User model serializer.

        Attributes:
            model (User): The model associated with the serializer.
            fields (tuple): The fields to be included in the serializer.
        """
        model = User
        fields = ('username', 'email',  'password', 'confirm_password')

    def validate(self, data):
        """
        Validate the input data for the User serializer.

        Args:
            data (dict): The input data to validate.

        Raises:
            serializers.ValidationError: If any validation check fails.

        Returns:
            dict: The validated data.
        """
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
        """
        Create a new User instance with the validated data.

        Args:
            validated_data (dict): The data that has been validated.

        Returns:
            User: The created User instance.
        """
        validated_data.pop('confirm_password')
        user = User.objects.create_user(**validated_data)
        return user
    
class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the Investor model.
    """
    class Meta:
        """
        Metaclass for the Investor contraints.
        """
    model = Investor
    fields = ['id', 'username', 'email']
        
class AccountSerializer(serializers.ModelSerializer):
    """
    Serializer for the Account model.
    """
    users = serializers.SlugRelatedField(slug_field='username', queryset=User.objects.all(), many=True, required=False)

    class Meta:
        """
        Metaclass for the Account contraints.
        """
        model = Account
        fields = ['id', 'name', 'description', 'users']
        
        def create(self, validated_data):
            """
            Method for creating users using username for slug field
            """
            users = validated_data.pop('users', []) 
            account = Account.objects.create(**validated_data)
            account.users.set(users) 
            return account
        
class AccountPermissionsSerializer(serializers.ModelSerializer):
    """
    Serializer for the Account Permissions model.
    """
    user = serializers.CharField()  
    account = serializers.CharField() 

    class Meta:
        """
        Metaclass for the AccountPermissions contraints.
        """
        model = AccountPermissions
        fields = ['id', 'user', 'account', 'permission']

    def validate(self, data):
        """
        Validate and convert usernames and account names to IDs.
        """
        user = User.objects.get(username=data['user'])
        account = Account.objects.get(name=data['account'])
        data['user'] = user
        data['account'] = account
        return data 
    
class AccountPermissionsUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating only the permission field of Account Permissions.
    """
    class Meta:
        """
        Metaclass contraints for updating user permissions.
        """
        model = AccountPermissions
        fields = ['permission']
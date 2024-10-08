from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from .models import AccountPermissions, Account
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.utils import timezone
import json

transaction_date = timezone.now()

class UserAuthTests(APITestCase):
    """
    Test case for user registration, login, and token-based access.
    """
    def setUp(self):
        """
        Set up tests
        """
        self.register_url = reverse('register')
        self.login_url = reverse('token_obtain_pair')
        self.user_data = {
            'username': 'testuser',
            'password': 'password123'
        }
        try:
            User.objects.get(username=self.user_data['username'])
        except ObjectDoesNotExist:
            User.objects.create_user(**self.user_data)
            User.objects.filter(username=self.user_data['username']).delete()
            
    def tearDown(self):
        """
        Delete user after tests
        """
        User.objects.filter(username=self.user_data['username']).delete()

    def test_user_registration(self):
        """
        Test the user registration process.
        """
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'StrongPassword123',
            'confirm_password': 'StrongPassword123'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'User registered successfully.')
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_user_login(self):
        """
        Test the user login process and token generation.
        """
        User.objects.create_user(**self.user_data)
        response = self.client.post(self.login_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_protected_view_with_token(self):
        """
        Test accessing a protected view using a valid token.
        """
        User.objects.create_user(**self.user_data)
        login_response = self.client.post(self.login_url, self.user_data)
    
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        access_token = login_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        account = Account.objects.create(name="Test Account", description="A test account")
        account.users.add(User.objects.get(username='testuser'))
        account_pk = account.pk
        protected_url = reverse('select-account', kwargs={'pk': account_pk})
        
        put_data = {
            'account_id': account_pk
        }
        response = self.client.put(protected_url, data=put_data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class AccountTests(APITestCase):
    """
    Test case for account creation, retrieval, and permission checks.
    """
    def setUp(self):
        """
        Create test users
        """
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.user1 = User.objects.create_user(username='testuser1', password='testpassword1')
        self.user2 = User.objects.create_user(username='testuser2', password='testpassword2')
        
        self.client.login(username='testuser1', password='testpassword1')
        
        refresh = RefreshToken.for_user(self.user1)
        self.token = str(refresh.access_token)
        
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)
        
        self.account = Account.objects.create(name='Test Account', description='A test account')
        self.account.users.add(self.user1, self.user2)
   
        self.url = reverse('account-list') 
        self.url_detail = reverse('account-detail', kwargs={'pk': self.account.pk}) 

    def test_create_account_with_users(self):
        """
        Test account creation with associated users and correct permission.
        """
        data = {
            'name': 'Test Investment Account',
            'description': 'This is a test account',
            'users': [self.user1.username, self.user2.username],
            'permission': 'full'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        account = Account.objects.get(name='Test Investment Account')
        self.assertIn(self.user1, account.users.all())
        self.assertIn(self.user2, account.users.all())
        account_permission = AccountPermissions.objects.get(user=self.user1, account=account)
        self.assertEqual(account_permission.permission, 'full')

    def test_create_account_without_authentication(self):
        """
        Test account creation without authentication.
        """
        self.client.credentials()  # Clear credentials
        response = self.client.post(self.url, {
            'name': 'Unauthorized Account',
            'description': 'This should not work'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_account(self):
        """
        Test retrieving an account.
        """
        self.assertTrue(Account.objects.filter(pk=self.account.pk).exists())
        response = self.client.get(self.url_detail)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Account')
        self.assertEqual(response.data['description'], 'A test account')

    def test_create_account_with_existing_name(self):
        """
        Test creating an account with an existing name.
        """
        self.admin_user = User.objects.create_superuser(username='admin', password='adminpass')
        login_response = self.client.post(reverse('token_obtain_pair'), {
            'username': 'admin',
            'password': 'adminpass'
        })
        self.assertEqual(login_response.status_code, status.HTTP_200_OK, "Login failed")
        access_token = login_response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + access_token)
        
        Account.objects.create(name='Duplicate Account')
        response = self.client.post(self.url, {
            'name': 'Duplicate Account',
            'description': 'Trying to duplicate'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)


class PermissionTests(APITestCase):
    """
    Test various permission levels for account access.
    """

    def setUp(self):
        """
        Set up the test environment by creating a user, an account, and assigning a token.
        """
        self.user1 = User.objects.create_user(username='testuser1', password='testpassword1')
        self.account = Account.objects.create(name='Test Account')
        self.account.users.add(self.user1)
        self.url = reverse('account-detail', kwargs={'pk': self.account.pk})
        
        refresh = RefreshToken.for_user(self.user1)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)

    def test_full_access_permission(self):
        """
        Test FULL_ACCESS permission functionality.
        Ensure that a user with full access can view account details.
        """
        AccountPermissions.objects.create(
            user=self.user1,
            account=self.account,
            permission=AccountPermissions.FULL_ACCESS
        )
        self.client.login(username='testuser1', password='testpassword1')

        permissions = AccountPermissions.objects.filter(user=self.user1, account=self.account)
        print(permissions)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

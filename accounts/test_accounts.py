from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from .models import AccountPermissions,Account
from django.urls import reverse
from rest_framework.test import APIClient

# Create your tests here.
class LoginTestCase(APITestCase):
    """
    A TestCase for user Login.
    """
    def __init__(self, *args, **kwargs):
        super(LoginTestCase, self).__init__(*args, **kwargs)
        self.user = None

    def set_up(self):
        """
        Set up Test environment with test user and test password.
        """
        self.user = User.objects.create_user(username="testuser", password="testpassword", is_active=True)

    def test_successful_login(self):
        """
        Test the login of a user using test username and password.
        A POST request is sent and if succesful a response is asserted with a status code of '200' and tokens 
        """
        url = reverse('login')
        data = {
            'username': 'testuser',
            'password': 'testpassword'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        
class RegistrationTestCase(APITestCase):
    """
    A TestCase for user User Account creation.
    """

    def test_successful_registration(self):
        """
        Test successful registration.
        A POST request containing the data variables is sent and 
        a 201 status asserted if the user exists.
        """
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'StrongPassword123',
            'confirm_password': 'StrongPassword123'
        }

        response = self.client.post(reverse('register'), data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        
class AccountCreationTest(APITestCase):
    """
    A TestCase for Transaction Account creation.
    """
    
    def __init__(self, *args, **kwargs):
        super(AccountCreationTest, self).__init__(*args, **kwargs)
        self.user = None
        
    def set_up(self):
        """
        Set up a user and authenticate the client.
        """
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')
    
    def test_create_account(self):
        """
        Test the account creation functionality.
        """
        url = reverse('accounts-list')
        data = {
            'name': 'Test Investment Account',
            'description': 'This is a test account',
            'permission': 'full'  
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        account = Account.objects.get(name='Test Investment Account')
        self.assertEqual(account.description, 'This is a test account')
        
        account_permission = AccountPermissions.objects.get(user=self.user, account=account)
        self.assertEqual(account_permission.permission, 'full')

    def test_default_permission(self):
        """
        Test account creation with default permission when 'permission' is not provided.
        """
        url = reverse('accounts-list')
        data = {
            'name': 'Default Permission Account',
            'description': 'Account with default permission'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        account = Account.objects.get(name='Default Permission Account')
        self.assertEqual(account.description, 'Account with default permission')

        account_permission = AccountPermissions.objects.get(user=self.user, account=account)
        self.assertEqual(account_permission.permission, AccountPermissions.VIEW_ONLY)
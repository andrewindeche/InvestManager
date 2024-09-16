from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from .models import AccountPermissions,Account
from django.urls import reverse

# Create your tests here.
class LoginTestCase(APITestCase):
    """
    Test case for user login functionality.
    """

    def setUp(self):
        """
        Set up a test user.
        """
        self.url = reverse('login') 
        self.user = User.objects.create_user(username='testuser', password='testpassword')

    def test_successful_login(self):
        """
        Test the login using a test username and password.
        """
        data = {
            'username': 'testuser',
            'password': 'testpassword'
        }
        response = self.client.post(self.url, data, format='json')
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
    A TestCase for Transaction Account creation and retrieval.
    """

    def setUp(self):
        """
        Set up users and authenticate the client.
        """
        self.user1 = User.objects.create_user(username='testuser1', password='testpassword1')
        self.user2 = User.objects.create_user(username='testuser2', password='testpassword2')
        self.client.login(username='testuser1', password='testpassword1')
        self.account = Account.objects.create(name='Test Account', description='A test account')
        self.account.users.add(self.user1, self.user2)
        self.url = reverse('account-detail', kwargs={'pk': self.account.pk})

    def test_create_account_with_users(self):
        """
        Test the account creation functionality with users added by username.
        """
        url = reverse('account-detail', kwargs={'pk': self.account.pk})
        data = {
            'name': 'Test Investment Account',
            'description': 'This is a test account',
            'users': ['testuser1', 'testuser2'],
            'permission': 'full'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        account = Account.objects.get(name='Test Investment Account')
        self.assertEqual(account.description, 'This is a test account')

        self.assertIn(self.user1, account.users.all())
        self.assertIn(self.user2, account.users.all())

        account_permission = AccountPermissions.objects.get(user=self.user1, account=account)
        self.assertEqual(account_permission.permission, 'full')

    def test_default_permission(self):
        """
        Test account creation with default permission when 'permission' is not provided.
        """
        url = reverse('account-detail', kwargs={'pk': self.account.pk})
        data = {
            'name': 'Default Permission Account',
            'description': 'Account with default permission',
            'users': ['testuser1']
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        account = Account.objects.get(name='Default Permission Account')
        self.assertEqual(account.description, 'Account with default permission')

        account_permission = AccountPermissions.objects.get(user=self.user1, account=account)
        self.assertEqual(account_permission.permission, AccountPermissions.VIEW_ONLY)

    def test_retrieve_account(self):
        """
        Test retrieving an account.
        """
        account = Account.objects.create(name='Retrieve Test Account', description='Test retrieval')
        account.users.add(self.user1, self.user2)

        url = reverse('account-detail', kwargs={'pk': self.account.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Retrieve Test Account')
        self.assertEqual(response.data['description'], 'Test retrieval')
        self.assertIn('testuser1', [user['username'] for user in response.data['users']])
        self.assertIn('testuser2', [user['username'] for user in response.data['users']])
        
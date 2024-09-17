from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from .models import AccountPermissions, Account
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
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client = APIClient()
        self.url = reverse('login')

    def test_user_login_and_token_generation(self):
        """
        Test the login and token generation functionality.
        """
        response = self.client.post(self.url, {'username': 'testuser', 'password': 'testpassword'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        token = Token.objects.get_or_create(user=self.user)
        
        self.assertIsNotNone(token)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        response = self.client.get(reverse('protected-view')) 
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_token_validation(self):
        """
        Validate token generation and test a protected view with the token.
        """
        token = Token.objects.get_or_create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        response = self.client.get('/api/protected-view/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_token(self):
        """
        Test validation of an invalid token.
        """
        self.client.credentials(HTTP_AUTHORIZATION='Token invalidtoken')
        response = self.client.get('/api/protected-view/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class RegistrationTestCase(APITestCase):
    """
    Test case for user account creation.
    """
    def test_successful_registration(self):
        """
        Test successful user registration.
        """
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'StrongPassword123',
            'confirm_password': 'StrongPassword123'
        }
        response = self.client.post(reverse('register'), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='newuser').exists())


class AccountTest(APITestCase):
    """
    Test case for account creation and retrieval.
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
        Test account creation with associated users.
        """
        data = {
            'name': 'Test Investment Account',
            'description': 'This is a test account',
            'users': ['testuser1', 'testuser2'],
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
        self.client.credentials()  # Remove authentication
        response = self.client.post('/api/accounts/', {
            'name': 'Unauthorized Account',
            'description': 'This should not work'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_account(self):
        """
        Test retrieving an account.
        """
        account = Account.objects.create(name='Retrieve Test Account', description='Test retrieval')
        account.users.add(self.user1, self.user2)

        response = self.client.get(reverse('account-detail', kwargs={'pk': account.pk}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Retrieve Test Account')
        self.assertEqual(response.data['description'], 'Test retrieval')

    def test_create_account_with_existing_name(self):
        """
        Test creating an account with an existing name.
        """
        Account.objects.create(name='Duplicate Account')

        response = self.client.post('/api/accounts/', {
            'name': 'Duplicate Account',
            'description': 'Trying to duplicate'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('name', response.data)


class PermissionTest(APITestCase):
    """
    Test various permission levels for account access.
    """
    def setUp(self):
        """
        Set up a test user and account for permission tests.
        """
        self.user1 = User.objects.create_user(username='testuser1', password='testpassword1')
        self.account = Account.objects.create(name='Test Account')
        self.account.users.add(self.user1)
        self.url = reverse('account-detail', kwargs={'pk': self.account.pk})

    def test_post_only_permission_post(self):
        """
        Test creating a transaction with POST-only permission.
        """
        self.client.login(username='testuser1', password='testpassword1')
        response = self.client.post(f'/api/accounts/{self.account.id}/transactions/', data={'amount': '500.00', 'symbol': 'TSLA'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_post_only_permission_get(self):
        """
        Test viewing transactions with POST-only permission (should fail).
        """
        self.client.login(username='testuser1', password='testpassword1')
        response = self.client.get(f'/api/accounts/{self.account.id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_full_access_permission_get(self):
        """
        Test viewing transactions with full access permission.
        """
        self.client.login(username='testuser1', password='testpassword1')
        response = self.client.get(f'/api/accounts/{self.account.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_view_only_permission_post(self):
        """
        Test creating a transaction with view-only permission (should fail).
        """
        self.client.login(username='testuser1', password='testpassword1')
        response = self.client.post(f'/api/accounts/{self.account.id}/transactions/', data={})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

from django.core.exceptions import PermissionDenied
from rest_framework.test import APITestCase
from decimal import Decimal
import json
from django.utils import timezone
from datetime import datetime
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Transaction, Account, SimulatedInvestment
from accounts.models import AccountPermissions
from .utils_permissions import create_transaction
from unittest.mock import patch

class UserTransactionsAdminTests(APITestCase):
    """
    Test the ability of an admin user to retrieve and filter transactions of a user.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.admin_user = None
        self.client = None
        self.url = '/api/transactions/'
    def setUp(self):
        """
        set up tests
        """
        self.client = APIClient()
        self.admin_user = User.objects.create_superuser(username='admin', password='adminpass')
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.account = Account.objects.create(name='Test Account')
        self.account.users.add(self.user)
        self.investment = SimulatedInvestment.objects.create(
            account=self.account,
            name='Test Investment',
            symbol='TSLA',
            units=10,
            price_per_unit=100,
        )
        self.transaction_date = timezone.make_aware(datetime.strptime('2024-01-01', '%Y-%m-%d'))
        self.transaction = Transaction.objects.create(
            user=self.user,
            account=self.account,
            transaction_date=self.transaction_date,
            amount=500
        )
        self.login_url = reverse('token_obtain_pair')
        login_response = self.client.post(
            self.login_url,
            {'username': 'admin',
             'password': 'adminpass'}
            )
        self.access_token = login_response.data['access']
        self.assertIsNotNone(self.access_token, "Access token not provided in response")
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        self.url = reverse('user-transactions-admin', kwargs={'username': self.user.username})
     
    def create_test_data(self):
        """
        Create simulated investments with test data
         """
        unique_account_name = f'Test Account {self._testMethodName}'
        self.account = Account.objects.create(name=unique_account_name)
        self.account.users.add(self.user)
        
        investment_1 = SimulatedInvestment.objects.create(
            account=self.account,
            name='Test Investment 1',
            symbol='AAPL',
            price_per_unit=Decimal('100'),
            units=10,
            transaction_type='buy'
        )
        
        investment_2 = SimulatedInvestment.objects.create(
            account=self.account,
            name='Test Investment 2',
            symbol='GOOGL',
            price_per_unit=Decimal('50'),
            units=20,
            transaction_type='buy'
        )
        
        Transaction.objects.create(
            user=self.user,
            account=self.account,
            investment=investment_1,
            amount=Decimal('1000'),
            transaction_date=timezone.now(),
            transaction_type='buy'
        )
        
        Transaction.objects.create(
            user=self.user,
            account=self.account,
            investment=investment_2,
            amount=Decimal('1000'),
            transaction_date=timezone.now(),
            transaction_type='buy'
        )

    def test_admin_user_can_retrieve_transactions(self):
        """
        Test that an admin user can retrieve transactions.
        """
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_transactions_invalid_user(self):
        """
        Test retrieving transactions for an invalid user.
        Verifies that a 404 Not Found status is returned.
        """
        invalid_url = reverse('user-transactions-admin', kwargs={'username': 'invaliduser'})
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

class SimulatedInvestmentTransactionTest(APITestCase):
    """
    Test suite for simulating buy/sell transactions for a user's account.
    """
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client = APIClient()
        self.client.login(username='testuser', password='testpassword')
        self.account = Account.objects.create(name='Test Account')
        self.account.users.add(self.user)
        self.url = reverse(
            'simulate-investment-transaction', 
            kwargs={'account_pk': self.account.pk})

class CreateTransactionTest(APITestCase):
    """
    Test suite for the create_transaction utility function.
    """
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.account = Account.objects.create(name='Test Account')
        self.account.users.add(self.user)
        self.investment = SimulatedInvestment.objects.create(
            account=self.account,
            name='Investment A',
            symbol='AAPL',
            price_per_unit=Decimal('100.00'),
            units=Decimal('10.00')
        )
        self.permission = AccountPermissions.objects.create(
            user=self.user,
            account=self.account,
            permission=AccountPermissions.FULL_ACCESS
            )

   

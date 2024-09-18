from django.core.exceptions import PermissionDenied
from rest_framework.test import APITestCase
from decimal import Decimal
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

    @patch('transactions.utils.fetch_market_data', return_value={'price': Decimal('100')})
    def test_get_transactions_with_and_without_date_filter(self, mock_fetch_market_data):
        """
        Test transactions with and without filter.
        """
        self.create_test_data()
        
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_investments'], Decimal('1000'))
        self.assertEqual(response.data['total_investments_in_kes'], Decimal('140000'))
        self.assertEqual(len(response.data['investments']), 1)

        mock_fetch_market_data.assert_called()

        start_date = timezone.make_aware(datetime.strptime('2024-01-01', '%Y-%m-%d'))
        end_date = timezone.make_aware(datetime.strptime('2024-12-31', '%Y-%m-%d'))

        response = self.client.get(
            self.url,
            {'start_date': start_date.isoformat(),
             'end_date': end_date.isoformat()}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_with_filter = self.client.get(self.transactions_url, {'date': '2024-09-18'})
        self.assertEqual(response_with_filter.status_code, status.HTTP_200_OK)

        expected_total_investments = Decimal('1000')
        expected_total_investments_in_kes = expected_total_investments * Decimal('140')
        self.assertEqual(response_with_filter.data['total_investments'], expected_total_investments)
        self.assertEqual(
            response_with_filter.data['total_investments_in_kes'],
            expected_total_investments_in_kes
        )
        self.assertEqual(len(response_with_filter.data['investments']), 2)

        mock_fetch_market_data.assert_called_with('AAPL')

        response_with_filter = self.client.get(self.transactions_url, {'date': '2024-09-18'})
        self.assertEqual(response_with_filter.status_code, status.HTTP_200_OK)

        expected_total_investments = Decimal('1000')
        expected_total_investments_in_kes = expected_total_investments * Decimal('140')
        self.assertEqual(response_with_filter.data['total_investments'], expected_total_investments)
        self.assertEqual(
            response_with_filter.data['total_investments_in_kes'],
            expected_total_investments_in_kes
        )
        self.assertEqual(len(response_with_filter.data['investments']), 2)

        mock_fetch_market_data.assert_called_with('AAPL')

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
        self.client.login(username='testuser', password='testpassword')
        self.account = Account.objects.create(name='Test Account')
        self.account.users.add(self.user)
        self.url = reverse(
            'simulate-investment-transaction', 
            kwargs={'account_pk': self.account.pk})

    def test_post_transaction_with_valid_data(self):
        """
        Ensure that a valid POST request simulates a buy/sell transaction successfully.
        """
        data = {
            'transaction_type': 'buy',
            'amount': '1000',
            'symbol': 'AAPL'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

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

    def test_create_and_validate_transaction(self):
        """
        Ensure that transactions are created correctly, and permission validations are enforced.
        """
        transaction = create_transaction(
            self.user, self.account,
            self.investment, Decimal('500.00'), 'buy')
        self.assertEqual(Transaction.objects.count(), 1)
        self.assertEqual(transaction.transaction_type, 'buy')
        self.assertEqual(self.investment.units, Decimal('15.00'))
        self.assertEqual(
            self.investment.total_value,
            self.investment.price_per_unit * self.investment.units
            )

        transaction = create_transaction(
            self.user,
            self.account,
            self.investment,
            Decimal('500.00'),
            'sell')
        self.assertEqual(Transaction.objects.count(), 2)
        self.assertEqual(transaction.transaction_type, 'sell')
        self.assertEqual(self.investment.units, Decimal('5.00'))
        self.assertEqual(
            self.investment.total_value,
            self.investment.price_per_unit * self.investment.units)

        with self.assertRaises(ValueError) as e:
            create_transaction(self.user, self.account, self.investment, Decimal('2000.00'), 'sell')
        self.assertEqual(str(e.exception), "Not enough units to sell.")
        self.assertEqual(Transaction.objects.count(), 2)
        with self.assertRaises(ValueError) as e:
            create_transaction(self.user, self.account, None, Decimal('500.00'), 'buy')
        self.assertEqual(str(e.exception), "Investment not found.")
        self.assertEqual(Transaction.objects.count(), 2)

        for permission, expected_exception in [
            (AccountPermissions.VIEW_ONLY, "You only have view-only access to this account."),
            (AccountPermissions.POST_ONLY, "You do not have permission to perform this action."),
            (None, "You do not have permission to access this account.")
        ]:
            self.permission.permission = (
                permission if permission is not None else AccountPermissions.NO_ACCESS
                )
            self.permission.save() if permission is not None else self.permission.delete()
            with self.assertRaises(PermissionDenied) as e:
                create_transaction(
                    self.user,
                    self.account,
                    self.investment,
                    Decimal('500.00'),
                    'buy'
                    )
            self.assertEqual(str(e.exception), expected_exception)
            self.assertEqual(Transaction.objects.count(), 2 if permission is None else 3)

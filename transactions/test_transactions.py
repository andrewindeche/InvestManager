from django.core.exceptions import PermissionDenied
from rest_framework.test import APITestCase
from decimal import Decimal
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Transaction, Account, SimulatedInvestment
from accounts.models import Account, AccountPermissions
from .utils_permissions import create_transaction

# Create your tests here.
class UserTransactionsAdminTests(APITestCase):
    """
    Test the ability of a user with admin view to retrieve transactions of a user and filter
    the transactions.
    """
    def setUp(self):
        """
        Set up the test environment, including creating a superuser, a regular user, an account, 
        an investment, and a transaction. Also, log in the admin user.
        """
        self.admin_user = User.objects.create_superuser(username='admin', password='adminpass')
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.account = Account.objects.create(name='Test Account')
        self.account.users.add(self.user)
        self.investment = SimulatedInvestment.objects.create(
            account=self.account,
            name='Test Investment',
            symbol='TST',
            units=10,
            price_per_unit=100,
            total_value=1000
        )
        self.transaction = Transaction.objects.create(
            user=self.user,
            transaction_date='2023-01-01',
            amount=500
        )
        self.client = APIClient()
        self.client.login(username='admin', password='adminpass')
        self.url = reverse('user-transactions-admin', kwargs={'username': self.user.username})
        
    def test_admin_user_can_retrieve_transactions(self):
        """
        Test user with admin rights retrieving transactions.
        Verifies that admin users can retrieve transactions.
        """
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_non_admin_user_cannot_access(self):
        """
        Test user with non-admin rights retrieving transactions.
        """
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_transactions_no_date_filter(self):
        """
        Test retrieving transactions without any date filters. 
        Verifies that the total investments and their value in KES are calculated correctly.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_investments'], Decimal('1000'))
        self.assertEqual(response.data['total_investments_in_kes'], Decimal('140000'))
        self.assertEqual(len(response.data['investments']), 1)

    def test_get_transactions_with_date_filter(self):
        """
        Test retrieving transactions with date filters. 
        Verifies that the total investments and their value in KES are calculated correctly.
        """
        response = self.client.get(self.url, {'start_date': '2023-01-01', 'end_date': '2023-12-31'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_investments'], Decimal('1000'))
        self.assertEqual(response.data['total_investments_in_kes'], Decimal('140000'))
        self.assertEqual(len(response.data['investments']), 1)

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
    Test suite for the SimulatedInvestmentTransactions.

    Tests the simulation of buy/sell transactions for a user's account.
    """
    def setUp(self):
        self.url = reverse('simulate-transaction', kwargs={'account_pk': self.account.pk})

    def test_post_transaction_with_valid_data(self):
        """
        Ensure that a valid POST request simulates a buy/sell transaction successfully.
        """
        self.client.force_authenticate(user=self.user)
        data = {
            'transaction_type': 'buy',
            'amount': '1000',
            'symbol': 'AAPL'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_transaction_with_invalid_amount(self):
        """
        Ensure that an invalid amount format results in a 400 Bad Request error.
        """
        self.client.force_authenticate(user=self.user)
        data = {
            'transaction_type': 'buy',
            'amount': 'invalid',
            'symbol': 'AAPL'
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
class CreateTransactionTest(APITestCase):
    """
    Test suite for the create_transaction utility function.

    This tests the proper creation of transactions with validation and permission checks.
    """

    def setUp(self):
        """
        Set up test data, including a user, account, investment, and associated permissions.
        """
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
        self.permission = AccountPermissions.objects.create(user=self.user, account=self.account, permission=AccountPermissions.FULL_ACCESS)

    def test_create_buy_transaction(self):
        """
        Ensure that a 'buy' transaction is successfully created for an investment with the correct permission.
        """
        transaction = create_transaction(self.user, self.account, self.investment, Decimal('500.00'), 'buy')
        self.assertEqual(Transaction.objects.count(), 1)
        self.assertEqual(transaction.transaction_type, 'buy')
        self.assertEqual(self.investment.units, Decimal('15.00'))

    def test_create_sell_transaction(self):
        """
        Ensure that a 'sell' transaction is successfully created, reducing the investment units.
        """
        transaction = create_transaction(self.user, self.account, self.investment, Decimal('500.00'), 'sell')
        self.assertEqual(Transaction.objects.count(), 1)
        self.assertEqual(transaction.transaction_type, 'sell')
        self.assertEqual(self.investment.units, Decimal('5.00')) 

    def test_sell_transaction_with_insufficient_units(self):
        """
        Ensure that selling more units than available raises a ValueError.
        """
        with self.assertRaises(ValueError) as e:
            create_transaction(self.user, self.account, self.investment, Decimal('2000.00'), 'sell')
        self.assertEqual(str(e.exception), "Not enough units to sell.")
        self.assertEqual(Transaction.objects.count(), 0) 

    def test_transaction_with_no_investment(self):
        """
        Ensure that a ValueError is raised if the investment is not found.
        """
        with self.assertRaises(ValueError) as e:
            create_transaction(self.user, self.account, None, Decimal('500.00'), 'buy')
        self.assertEqual(str(e.exception), "Investment not found.")
        self.assertEqual(Transaction.objects.count(), 0)

    def test_transaction_with_view_only_permission(self):
        """
        Ensure that a user with VIEW_ONLY permission cannot perform transactions.
        """
        self.permission.permission = AccountPermissions.VIEW_ONLY
        self.permission.save()
        with self.assertRaises(PermissionDenied) as e:
            create_transaction(self.user, self.account, self.investment, Decimal('500.00'), 'buy')
        self.assertEqual(str(e.exception), "You only have view-only access to this account.")
        self.assertEqual(Transaction.objects.count(), 0)

    def test_transaction_with_post_only_permission(self):
        """
        Ensure that a user with POST_ONLY permission cannot perform a 'buy' transaction.
        """
        self.permission.permission = AccountPermissions.POST_ONLY
        self.permission.save()
        with self.assertRaises(PermissionDenied) as e:
            create_transaction(self.user, self.account, self.investment, Decimal('500.00'), 'buy')
        self.assertEqual(str(e.exception), "You do not have permission to perform this action.")
        self.assertEqual(Transaction.objects.count(), 0)

    def test_transaction_with_no_permission(self):
        """
        Ensure that a user with no permissions cannot access the account for a transaction.
        """
        self.permission.delete()
        with self.assertRaises(PermissionDenied) as e:
            create_transaction(self.user, self.account, self.investment, Decimal('500.00'), 'buy')
        self.assertEqual(str(e.exception), "You do not have permission to access this account.")
        self.assertEqual(Transaction.objects.count(), 0)
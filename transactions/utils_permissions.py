from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from decimal import Decimal
from rest_framework.exceptions import ValidationError
from accounts.models import Account, AccountPermissions
from .models import Transaction, SimulatedInvestment
from .utils import fetch_market_data

def process_transaction(user, account_pk, transaction_type, amount, symbol):
    """
    Process a buy/sell transaction, including permission checks and investment updates.
    """
    account = get_object_or_404(Account, pk=account_pk, users=user)
    account.balance = Decimal('20000.00')  
    account.save()
    
    permission = AccountPermissions.objects.filter(user=user, account=account).first()
    if permission is None:
        raise PermissionDenied("You do not have permission to access this account")

    if permission.permission == AccountPermissions.VIEW_ONLY:
        raise PermissionDenied("You only have view permissions for this account")
    
    if permission.permission == AccountPermissions.POST_ONLY and transaction_type == 'buy':
        raise PermissionDenied("You do not have permission to perform this action")

    market_data = fetch_market_data(symbol)
    if 'error' in market_data:
        raise ValidationError(market_data['error'])

    price_per_unit = market_data.get('price')
    if price_per_unit is None:
        raise ValidationError("Price data not available")

    try:
        price_per_unit = Decimal(price_per_unit)
    except (ValueError, TypeError):
        raise ValidationError("Price data is invalid")

    investment_value = None
    try:
        investment, created = SimulatedInvestment.objects.get_or_create(
            account=account,
            symbol=symbol,
            defaults={'name': symbol, 'units': Decimal(amount) / price_per_unit, 'transaction_type': transaction_type}
        )
        if not created:
            if transaction_type == 'buy':
                investment.units += Decimal(amount) / price_per_unit
            elif transaction_type == 'sell':
                if investment.units < Decimal(amount) / price_per_unit:
                    raise ValueError("Not enough units to sell.")
                investment.units -= Decimal(amount) / price_per_unit
            investment.save()
            investment_value = Decimal(amount) * price_per_unit

        transaction = Transaction(
            user=user,
            account=account,
            investment=investment,
            amount=Decimal(amount),
            transaction_type=transaction_type
        )
        transaction.save()
    except IntegrityError:
        raise ValidationError('Duplicate investment entry detected')

    account.save()
    return investment, investment_value

def create_transaction(user, account, investment, amount, transaction_type):
    """
    Creates a transaction with proper validation and checks.
    """
    account_permission = AccountPermissions.objects.filter(user=user, account=account).first()

    if not account_permission:
        raise PermissionDenied("You do not have permission to access this account.")
    
    if account_permission.permission == AccountPermissions.VIEW_ONLY:
        raise PermissionDenied("You only have view-only access to this account.")
    
    if account_permission.permission == AccountPermissions.POST_ONLY and transaction_type == 'buy':
        raise PermissionDenied("You do not have permission to perform this action.")

    if investment:
        price_per_unit = Decimal(investment.price_per_unit)  # Convert to Decimal
        amount = Decimal(amount)  # Ensure amount is Decimal

        if transaction_type == 'buy':
            investment.units += amount / price_per_unit
        elif transaction_type == 'sell':
            if investment.units < amount / price_per_unit:
                raise ValueError("Not enough units to sell.")
            investment.units -= amount / price_per_unit
        else:
            raise ValueError("Invalid transaction type")

        investment.save()

        transaction = Transaction(
            user=user,
            account=account,
            investment=investment,
            amount=amount,
            transaction_type=transaction_type
        )
        transaction.save()
    else:
        raise ValueError("Investment not found.")

    return transaction

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.db import IntegrityError, transaction
from decimal import Decimal
from rest_framework.exceptions import ValidationError
from accounts.models import Account, AccountPermissions
from .models import Transaction, SimulatedInvestment
from .utils import fetch_market_data

@transaction.atomic
def process_transaction(user, account_pk, transaction_type, units, symbol):
    """
    Process a buy/sell transaction, including permission checks and investment updates.
    """
    account = get_object_or_404(Account, pk=account_pk, users=user)
    permission = AccountPermissions.objects.filter(user=user, account=account).first()
    
    if permission is None:
        raise PermissionDenied("You do not have permission to access this account")

    if permission.permission == AccountPermissions.VIEW_ONLY:
        raise PermissionDenied("You only have view permissions for this account")

    market_data = fetch_market_data(symbol)
    if 'error' in market_data:
        raise ValidationError(market_data['error'])

    price_per_unit = market_data.get('price')
    if price_per_unit is None:
        raise ValidationError("Price data not available")

    try:
        price_per_unit = Decimal(price_per_unit)
    except (ValueError, TypeError) as exc:
        raise ValidationError("Price data is invalid") from exc

    investment= SimulatedInvestment.objects.get_or_create(
        account=account,
        symbol=symbol,
        defaults={'name': symbol, 'units': Decimal(0), 'price_per_unit': price_per_unit}
    )

    investment_value = Decimal(units) * price_per_unit  # Calculate value for transaction

    if transaction_type == 'buy':
        investment.units += Decimal(units)
    elif transaction_type == 'sell':
        if investment.units < Decimal(units):
            raise ValueError("Not enough units to sell.")
        investment.units -= Decimal(units)
    
    investment.save()  

    transaction_record = Transaction(
        user=user,
        account=account,
        investment=investment,
        amount=investment_value,
        transaction_type=transaction_type
    )
    transaction_record.save() 

    return {
        'investment': investment,
        'investment_value': investment_value
    }
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
        try:
            price_per_unit = Decimal(investment.price_per_unit)
            amount = Decimal(amount)

            if transaction_type == 'buy':
                investment.units += amount / price_per_unit
            elif transaction_type == 'sell':
                if investment.units < amount / price_per_unit:
                    raise ValueError("Not enough units to sell.")
                investment.units -= amount / price_per_unit
            else:
                raise ValueError("Invalid transaction type")

            investment.save()

            new_transaction = Transaction(
                user=user,
                account=account,
                investment=investment,
                amount=amount,
                transaction_type=transaction_type
            )
            new_transaction.save()
        except ValueError as exc:
            raise ValidationError("Invalid value provided") from exc
        except IntegrityError as exc:
            raise IntegrityError("Database error occurred") from exc
    else:
        raise ValueError("Investment not found.")

    return new_transaction

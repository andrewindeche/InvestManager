from django.core.exceptions import PermissionDenied
from .models import Transaction, AccountPermissions

def create_transaction(user, account, investment, amount, transaction_type):
    """
    Creates a transaction with proper validation and checks.
    """
    # Fetch the user's permissions for the account
    account_permission = AccountPermissions.objects.filter(user=user, account=account).first()

    if not account_permission:
        raise PermissionDenied("You do not have permission to access this account.")
    
    if account_permission.permission == AccountPermissions.VIEW_ONLY:
        raise PermissionDenied("You only have view-only access to this account.")
    
    if account_permission.permission == AccountPermissions.POST_ONLY and transaction_type == 'buy':
        raise PermissionDenied("You do not have permission to perform this action.")

    # Check the investment and perform the transaction
    if investment:
        if transaction_type == 'buy':
            investment.units += amount / investment.price_per_unit
        elif transaction_type == 'sell':
            if investment.units < amount / investment.price_per_unit:
                raise ValueError("Not enough units to sell.")
            investment.units -= amount / investment.price_per_unit
        investment.save()

        # Create the transaction record
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

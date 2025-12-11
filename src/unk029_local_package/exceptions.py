"""
Custom exceptions for banking operations.
"""


class AccountError(Exception):
    """Base exception for account operations."""


class AccountNotFoundError(AccountError):
    """Raised when account is not found."""

    def __init__(self, account_no: int):
        self.account_no = account_no
        super().__init__(f"Account {account_no} not found")



class InsufficientFundsError(AccountError):
    """Raised when withdrawal exceeds balance."""

    def __init__(self, account_no: int, balance: float, amount: float):
        self.account_no = account_no
        self.balance = balance
        self.amount = amount
        super().__init__(f"Insufficient funds: balance {balance}, requested {amount}")


class InvalidPasswordError(AccountError):
    """Raised when password is invalid during login."""
    def __init__(self):
        super().__init__("Invalid password")

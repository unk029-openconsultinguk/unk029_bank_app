"""
unk029 - Bank Account Management Library

A reusable Python library for banking operations with Oracle database.

Usage:
    from unk029 import get_account, create_account, topup_account, withdraw_account
    from unk029 import DatabaseConfig, AccountCreate, TopUp, WithDraw
    
    # Use with environment variables (default)
    account = get_account(1001)
    
    # Or with custom config
    config = DatabaseConfig(user="myuser", password="mypass", dsn="mydsn")
    account = get_account(1001, config=config)
"""

from unk029.__about__ import __version__
from unk029.accounts import (
    # Exceptions
    AccountError,
    AccountNotFoundError,
    InsufficientFundsError,
    # Models
    AccountCreate,
    TopUp,
    WithDraw,
    Account,
    # Configuration
    DatabaseConfig,
    # Functions
    get_account,
    create_account,
    topup_account,
    withdraw_account,
)

__all__ = [
    # Version
    "__version__",
    # Exceptions
    "AccountError",
    "AccountNotFoundError", 
    "InsufficientFundsError",
    # Models
    "AccountCreate",
    "TopUp",
    "WithDraw",
    "Account",
    # Configuration
    "DatabaseConfig",
    # Functions
    "get_account",
    "create_account",
    "topup_account",
    "withdraw_account",
]
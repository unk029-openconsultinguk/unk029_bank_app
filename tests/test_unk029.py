"""Tests for unk029 library models and exceptions."""

import pytest

from unk029 import (
    Account,
    AccountCreate,
    AccountNotFoundError,
    Deposit,
    InsufficientFundsError,
    WithDraw,
)
from unk029.database import DatabaseConfig


def test_account_create_model() -> None:
    """Test AccountCreate model creation."""
    account = AccountCreate(
        name="John Doe",
        email="john@example.com",
        password="secret123",
    )
    assert account.name == "John Doe"
    assert account.email == "john@example.com"
    assert account.password == "secret123"


def test_account_create_required_fields() -> None:
    """Test AccountCreate model with all required fields."""
    account = AccountCreate(
        name="Jane Doe", email="jane@example.com", password="pass123"
    )
    assert account.name == "Jane Doe"
    assert account.email == "jane@example.com"
    assert account.password == "pass123"


def test_deposit_model() -> None:
    """Test Deposit model creation."""
    deposit = Deposit(amount=50.0)
    assert deposit.amount == 50.0


def test_withdraw_model() -> None:
    """Test WithDraw model creation."""
    withdraw = WithDraw(amount=25.0)
    assert withdraw.amount == 25.0


def test_account_model() -> None:
    """Test Account model creation."""
    account = Account(account_no=123, name="John Doe", balance=500.0, sortcode="12-34-56")
    assert account.account_no == 123
    assert account.name == "John Doe"
    assert account.balance == 500.0
    assert account.sortcode == "12-34-56"


def test_database_config_defaults() -> None:
    """Test DatabaseConfig with default values."""
    config = DatabaseConfig()
    # Config should be created without errors
    assert isinstance(config, DatabaseConfig)


def test_account_not_found_error() -> None:
    """Test AccountNotFoundError exception."""
    with pytest.raises(AccountNotFoundError) as exc_info:
        raise AccountNotFoundError(123)
    assert exc_info.value.account_no == 123
    assert "Account 123 not found" in str(exc_info.value)


def test_insufficient_funds_error() -> None:
    """Test InsufficientFundsError exception."""
    with pytest.raises(InsufficientFundsError) as exc_info:
        raise InsufficientFundsError(account_no=123, balance=50.0, amount=100.0)
    assert exc_info.value.account_no == 123
    assert exc_info.value.balance == 50.0
    assert exc_info.value.amount == 100.0
    assert "Insufficient funds" in str(exc_info.value)

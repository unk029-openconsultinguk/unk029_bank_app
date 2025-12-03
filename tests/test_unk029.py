"""Tests for unk029 library models and exceptions."""

import pytest

from unk029 import (
    Account,
    AccountCreate,
    AccountNotFoundError,
    InsufficientFundsError,
    TopUp,
    WithDraw,
)
from unk029.database import DatabaseConfig


def test_account_create_model() -> None:
    """Test AccountCreate model creation."""
    account = AccountCreate(
        name="John Doe",
        balance=100.0,
        password="secret123",
    )
    assert account.name == "John Doe"
    assert account.balance == 100.0
    assert account.password == "secret123"


def test_account_create_default_balance() -> None:
    """Test AccountCreate model with default balance."""
    account = AccountCreate(name="Jane Doe", password="pass123")
    assert account.name == "Jane Doe"
    assert account.balance == 0.0


def test_topup_model() -> None:
    """Test TopUp model creation."""
    topup = TopUp(amount=50.0)
    assert topup.amount == 50.0


def test_withdraw_model() -> None:
    """Test WithDraw model creation."""
    withdraw = WithDraw(amount=25.0)
    assert withdraw.amount == 25.0


def test_account_model() -> None:
    """Test Account model creation."""
    account = Account(account_no=123, name="John Doe", balance=500.0)
    assert account.account_no == 123
    assert account.name == "John Doe"
    assert account.balance == 500.0


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

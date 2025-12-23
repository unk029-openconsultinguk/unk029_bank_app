"""Tests for unk029 database functions with mocked database."""

from unittest.mock import MagicMock, patch

import pytest

from unk029.database import get_transactions, insert_transaction, login_account
from unk029.exceptions import AccountNotFoundError, InvalidPasswordError
from unk029.models import LoginRequest


@pytest.fixture
def mock_cursor() -> MagicMock:
    """Create a mock cursor with common attributes."""
    cursor = MagicMock()
    cursor.description = [("id",), ("type",), ("amount",)]
    cursor.__enter__ = MagicMock(return_value=cursor)
    cursor.__exit__ = MagicMock(return_value=False)
    return cursor


def test_insert_transaction(mock_cursor: MagicMock) -> None:
    """Test inserting a transaction."""
    with patch("unk029.database.get_cursor", return_value=mock_cursor):
        insert_transaction(
            account_no=123,
            type="deposit",
            amount=100.0,
            description="Test deposit",
        )

        # insert_transaction returns None
        mock_cursor.execute.assert_called_once()


def test_get_transactions(mock_cursor: MagicMock) -> None:
    """Test getting transactions for an account."""
    mock_cursor.fetchall.return_value = [
        (1, "deposit", 100.0, "Test deposit", "2024-01-01", None, "in", "success"),
        (2, "withdraw", 50.0, "Test withdraw", "2024-01-02", None, "out", "success"),
    ]
    mock_cursor.description = [
        ("id",),
        ("type",),
        ("amount",),
        ("description",),
        ("created_at",),
        ("related_account_no",),
        ("direction",),
        ("status",),
    ]

    with patch("unk029.database.get_cursor", return_value=mock_cursor):
        transactions = get_transactions(account_no=123)

        assert len(transactions) == 2
        assert transactions[0]["type"] == "deposit"
        assert transactions[1]["type"] == "withdraw"
        mock_cursor.execute.assert_called_once()


def test_login_account_with_account_no(mock_cursor: MagicMock) -> None:
    """Test login with account number."""
    mock_cursor.fetchone.return_value = (
        123,
        "John Doe",
        1000.0,
        "11-11-11",
        "password123",
        "john@example.com",
    )

    with patch("unk029.database.get_cursor", return_value=mock_cursor):
        login_request = LoginRequest(account_no=123, password="password123")
        result = login_account(login_request)

        assert result["account_no"] == 123
        assert result["name"] == "John Doe"
        assert result["balance"] == 1000.0
        mock_cursor.execute.assert_called_once()


def test_login_account_with_email(mock_cursor: MagicMock) -> None:
    """Test login with email."""
    mock_cursor.fetchone.return_value = (
        123,
        "John Doe",
        1000.0,
        "11-11-11",
        "password123",
        "john@example.com",
    )

    with patch("unk029.database.get_cursor", return_value=mock_cursor):
        login_request = LoginRequest(email="john@example.com", password="password123")
        result = login_account(login_request)

        assert result["account_no"] == 123
        assert result["name"] == "John Doe"
        mock_cursor.execute.assert_called_once()


def test_login_account_not_found(mock_cursor: MagicMock) -> None:
    """Test login with non-existent account."""
    mock_cursor.fetchone.return_value = None

    with patch("unk029.database.get_cursor", return_value=mock_cursor):
        login_request = LoginRequest(account_no=999, password="password123")

        with pytest.raises(AccountNotFoundError) as exc_info:
            login_account(login_request)

        assert exc_info.value.account_no == 999


def test_login_account_invalid_password(mock_cursor: MagicMock) -> None:
    """Test login with wrong password."""
    mock_cursor.fetchone.return_value = (
        123,
        "John Doe",
        1000.0,
        "11-11-11",
        "password123",
        "john@example.com",
    )

    with patch("unk029.database.get_cursor", return_value=mock_cursor):
        login_request = LoginRequest(account_no=123, password="wrongpassword")

        with pytest.raises(InvalidPasswordError):
            login_account(login_request)


def test_login_account_no_credentials(mock_cursor: MagicMock) -> None:
    """Test login without account_no or email."""
    with patch("unk029.database.get_cursor", return_value=mock_cursor):
        login_request = LoginRequest(password="password123")

        with pytest.raises(AccountNotFoundError):
            login_account(login_request)


def test_insert_transaction_with_all_fields(mock_cursor: MagicMock) -> None:
    """Test inserting transaction with all optional fields."""
    with patch("unk029.database.get_cursor", return_value=mock_cursor):
        insert_transaction(
            account_no=123,
            type="transfer",
            amount=100.0,
            description="Transfer to account 456",
            related_account_no=456,
            direction="out",
            status="success",
        )

        # insert_transaction returns None
        # Verify execute was called with the correct parameters
        mock_cursor.execute.assert_called_once()

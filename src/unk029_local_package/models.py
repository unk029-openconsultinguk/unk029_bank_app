"""
Bank Account Models
Pydantic models for banking operations.
"""

from pydantic import BaseModel


class AccountCreate(BaseModel):
    """Model for creating a new account."""

    name: str
    email: str
    password: str


class Deposit(BaseModel):
    """Model for deposit operation."""

    amount: float


class WithDraw(BaseModel):
    """Model for withdrawal operation."""

    amount: float


class LoginRequest(BaseModel):
    account_no: int | None = None
    email: str | None = None
    password: str


class Account(BaseModel):
    """Model representing a bank account."""

    account_no: int
    name: str
    balance: float
    sortcode: str


class Transfer(BaseModel):
    """Model for a transfer operation."""

    from_account_no: int
    to_account_no: int
    amount: float


class UniversalTransfer(BaseModel):
    """Unified model for both internal and external transfers."""

    from_account_no: int
    to_account_no: int
    amount: float
    to_sort_code: str | None = None
    to_name: str | None = "Recipient"


class PayeeCreate(BaseModel):
    user_account_no: int
    payee_name: str
    payee_account_no: int
    payee_sort_code: str


class Payee(BaseModel):
    id: int
    user_account_no: int
    payee_name: str
    payee_account_no: int
    payee_sort_code: str
    created_at: str


class AccountUpdate(BaseModel):
    """Model for updating account details."""

    email: str | None = None
    mobile: str | None = None
    password: str | None = None

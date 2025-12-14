"""
Bank Account Models
Pydantic models for banking operations.
"""

from pydantic import BaseModel


class AccountCreate(BaseModel):
    """Model for creating a new account."""

    name: str
    balance: float = 0.0
    password: str
    sortcode: str = "00-00-00"


class TopUp(BaseModel):
    """Model for deposit operation."""

    amount: float


class WithDraw(BaseModel):
    """Model for withdrawal operation."""

    amount: float


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

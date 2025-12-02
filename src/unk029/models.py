"""
Pydantic models for banking operations.
"""

from pydantic import BaseModel


class AccountCreate(BaseModel):
    """Model for creating a new account."""
    name: str
    balance: float = 0.0
    password: str


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

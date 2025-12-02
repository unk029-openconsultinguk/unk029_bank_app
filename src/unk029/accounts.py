"""
Bank Account Management Module
Provides reusable banking operations for Oracle database.
Can be configured with custom database credentials.
"""

import oracledb
import os
from dotenv import load_dotenv
from contextlib import contextmanager
from pydantic import BaseModel
from typing import Optional, Dict, Any

load_dotenv()


# ============== Exceptions ==============

class AccountError(Exception):
    """Base exception for account operations."""
    pass

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
        super().__init__(f"Insufficient funds: balance £{balance}, requested £{amount}")


# ============== Models ==============

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


# ============== Database Configuration ==============

class DatabaseConfig:
    """Database configuration holder."""
    def __init__(
        self,
        user: Optional[str] = None,
        password: Optional[str] = None,
        dsn: Optional[str] = None
    ):
        self.user = user or os.getenv("ORACLE_USER")
        self.password = password or os.getenv("ORACLE_PASSWORD")
        self.dsn = dsn or os.getenv("ORACLE_DSN")
    
    def validate(self) -> bool:
        """Check if all required config is present."""
        return all([self.user, self.password, self.dsn])


# Default configuration (uses environment variables)
_default_config = DatabaseConfig()


# ============== Database Connection ==============

def get_connection(config: Optional[DatabaseConfig] = None):
    """Get Oracle database connection."""
    cfg = config or _default_config
    return oracledb.connect(user=cfg.user, password=cfg.password, dsn=cfg.dsn)

@contextmanager
def get_cursor(config: Optional[DatabaseConfig] = None):
    """Context manager for database cursor."""
    conn = get_connection(config)
    cur = conn.cursor()
    try:
        yield cur
        conn.commit()
    finally:
        cur.close()
        conn.close()


# ============== Banking Operations ==============

def get_account(account_no: int, config: Optional[DatabaseConfig] = None) -> Dict[str, Any]:
    """Get account details by account number."""
    with get_cursor(config) as cur:
        cur.execute(
            "SELECT account_no, name, balance FROM accounts WHERE account_no = :id",
            {"id": account_no}
        )
        row = cur.fetchone()
        if row:
            return {"account_no": row[0], "name": row[1], "balance": row[2]}
        raise AccountNotFoundError(account_no)


def create_account(account: AccountCreate, config: Optional[DatabaseConfig] = None) -> Dict[str, Any]:
    """Create a new bank account."""
    with get_cursor(config) as cur:
        # Get next account number
        cur.execute("SELECT MAX(account_no) FROM accounts")
        max_id = cur.fetchone()[0] or 1000
        account_no = max_id + 1
        
        # Insert new account
        cur.execute(
            "INSERT INTO accounts (account_no, name, balance, password) VALUES (:id, :name, :balance, :password)",
            {"id": account_no, "name": account.name, "balance": account.balance, "password": account.password}
        )
        return {"account_no": account_no, "name": account.name, "balance": account.balance}


def topup_account(account_no: int, topup: TopUp, config: Optional[DatabaseConfig] = None) -> Dict[str, Any]:
    """Deposit funds into an account."""
    with get_cursor(config) as cur:
        cur.execute(
            "SELECT name, balance FROM accounts WHERE account_no = :id",
            {"id": account_no}
        )
        row = cur.fetchone()
        if not row:
            raise AccountNotFoundError(account_no)
        
        name, balance = row
        new_balance = balance + topup.amount
        cur.execute(
            "UPDATE accounts SET balance = :balance WHERE account_no = :id",
            {"balance": new_balance, "id": account_no}
        )
        return {"account_no": account_no, "name": name, "new_balance": new_balance}


def withdraw_account(account_no: int, withdraw: WithDraw, config: Optional[DatabaseConfig] = None) -> Dict[str, Any]:
    """Withdraw funds from an account."""
    with get_cursor(config) as cur:
        cur.execute(
            "SELECT name, balance FROM accounts WHERE account_no = :id",
            {"id": account_no}
        )
        row = cur.fetchone()
        if not row:
            raise AccountNotFoundError(account_no)
        
        name, balance = row
        if withdraw.amount > balance:
            raise InsufficientFundsError(account_no, balance, withdraw.amount)
        
        new_balance = balance - withdraw.amount
        cur.execute(
            "UPDATE accounts SET balance = :balance WHERE account_no = :id",
            {"balance": new_balance, "id": account_no}
        )
        return {"account_no": account_no, "name": name, "new_balance": new_balance}

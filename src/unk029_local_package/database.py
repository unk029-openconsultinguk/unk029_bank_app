"""
Database configuration and connection management for Oracle.
"""

from collections.abc import Generator
from contextlib import contextmanager
import os
from typing import Any

from dotenv import load_dotenv
import oracledb
from unk029.exceptions import AccountNotFoundError, InsufficientFundsError
from unk029.models import AccountCreate, TopUp, Transfer, WithDraw

load_dotenv()


class DatabaseConfig:
    """Database configuration holder."""

    def __init__(
        self, user: str | None = None, password: str | None = None, dsn: str | None = None
    ):
        self.user = user or os.getenv("ORACLE_USER")
        self.password = password or os.getenv("ORACLE_PASSWORD")
        self.dsn = dsn or os.getenv("ORACLE_DSN")

    def validate(self) -> bool:
        """Check if all required config is present."""
        return all([self.user, self.password, self.dsn])


# Default configuration (uses environment variables)
_default_config = DatabaseConfig()


def get_connection(config: DatabaseConfig | None = None) -> oracledb.Connection:
    """Get Oracle database connection."""
    cfg = config or _default_config
    return oracledb.connect(user=cfg.user, password=cfg.password, dsn=cfg.dsn)


@contextmanager
def get_cursor(config: DatabaseConfig | None = None) -> Generator[oracledb.Cursor, None, None]:
    """Context manager for database cursor."""
    conn = get_connection(config)
    cur = conn.cursor()
    try:
        yield cur
        conn.commit()
    finally:
        cur.close()
        conn.close()


# ============== Database Operations ==============


def get_account(account_no: int, config: DatabaseConfig | None = None) -> dict[str, Any]:
    """Get account details by account number."""
    with get_cursor(config) as cur:
        cur.execute(
            (
                "SELECT account_no, name, balance, sortcode, password, email "
                "FROM accounts WHERE account_no = :id"
            ),
            {"id": account_no},
        )
        row = cur.fetchone()
        if row:
            return {
                "account_no": row[0],
                "name": row[1],
                "balance": row[2],
                "sortcode": row[3],
                "password": row[4],
                "email": row[5],
            }
        raise AccountNotFoundError(account_no)


def create_account(account: AccountCreate, config: DatabaseConfig | None = None) -> dict[str, Any]:
    """Create a new bank account."""
    with get_cursor(config) as cur:
        # Get next account number
        cur.execute("SELECT MAX(account_no) FROM accounts")
        max_id = cur.fetchone()[0] or 1000
        account_no = max_id + 1

        # Insert new account
        cur.execute(
            "INSERT INTO accounts (account_no, name, balance, password, sortcode, email) "
            "VALUES (:id, :name, :balance, :password, :sortcode, :email)",
            {
                "id": account_no,
                "name": account.name,
                "balance": account.balance,
                "password": account.password,
                "sortcode": account.sortcode,
                "email": getattr(account, "email", None),
            },
        )
        return {
            "account_no": account_no,
            "name": account.name,
            "balance": account.balance,
            "sortcode": account.sortcode,
            "password": account.password,
            "email": getattr(account, "email", None),
        }


def topup_account(
    account_no: int, topup: TopUp, config: DatabaseConfig | None = None
) -> dict[str, Any]:
    """Deposit funds into an account."""
    with get_cursor(config) as cur:
        cur.execute(
            "SELECT name, balance FROM accounts WHERE account_no = :id", {"id": account_no}
        )
        row = cur.fetchone()
        if not row:
            raise AccountNotFoundError(account_no)

        name, balance = row
        new_balance = balance + topup.amount
        cur.execute(
            "UPDATE accounts SET balance = :balance WHERE account_no = :id",
            {"balance": new_balance, "id": account_no},
        )
        return {"account_no": account_no, "name": name, "new_balance": new_balance}


def withdraw_account(
    account_no: int, withdraw: WithDraw, config: DatabaseConfig | None = None
) -> dict[str, Any]:
    """Withdraw funds from an account."""
    with get_cursor(config) as cur:
        cur.execute(
            "SELECT name, balance FROM accounts WHERE account_no = :id", {"id": account_no}
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
            {"balance": new_balance, "id": account_no},
        )
        return {"account_no": account_no, "name": name, "new_balance": new_balance}


def transfer_account(transfer: Transfer, config: DatabaseConfig | None = None) -> dict[str, Any]:
    """Transfer funds from one account to another."""
    with get_cursor(config) as cur:
        # Withdraw from source account
        cur.execute(
            "SELECT name, balance FROM accounts WHERE account_no = :id",
            {"id": transfer.from_account_no},
        )
        from_row = cur.fetchone()
        if not from_row:
            raise AccountNotFoundError(transfer.from_account_no)
        from_name, from_balance = from_row
        if transfer.amount > from_balance:
            raise InsufficientFundsError(transfer.from_account_no, from_balance, transfer.amount)

        # Check destination account
        cur.execute(
            "SELECT name, balance FROM accounts WHERE account_no = :id",
            {"id": transfer.to_account_no},
        )
        to_row = cur.fetchone()
        if not to_row:
            raise AccountNotFoundError(transfer.to_account_no)
        to_name, to_balance = to_row

        # Perform transfer
        new_from_balance = from_balance - transfer.amount
        new_to_balance = to_balance + transfer.amount

        cur.execute(
            "UPDATE accounts SET balance = :balance WHERE account_no = :id",
            {"balance": new_from_balance, "id": transfer.from_account_no},
        )
        cur.execute(
            "UPDATE accounts SET balance = :balance WHERE account_no = :id",
            {"balance": new_to_balance, "id": transfer.to_account_no},
        )

        return {
            "from_account_no": transfer.from_account_no,
            "to_account_no": transfer.to_account_no,
            "transfered_amount": transfer.amount,
            "from_new_balance": new_from_balance,
            "to_new_balance": new_to_balance,
        }


def insert_transaction(
    account_no: int,
    type: str,
    amount: float,
    description: str = None,
    related_account_no: int = None,
    direction: str = None,
    config: DatabaseConfig | None = None
) -> None:
    """Insert a transaction record."""
    with get_cursor(config) as cur:
        cur.execute(
            """
            INSERT INTO transactions (account_no, type, amount, description, related_account_no, direction)
            VALUES (:account_no, :type, :amount, :description, :related_account_no, :direction)
            """,
            {
                "account_no": account_no,
                "type": type,
                "amount": amount,
                "description": description,
                "related_account_no": related_account_no,
                "direction": direction,
            },
        )


def get_transactions(account_no: int, config: DatabaseConfig | None = None) -> list[dict[str, Any]]:
    """Fetch all transactions for an account, most recent first."""
    with get_cursor(config) as cur:
        cur.execute(
            """
            SELECT id, type, amount, description, created_at, related_account_no, direction
            FROM transactions
            WHERE account_no = :account_no
            ORDER BY created_at DESC
            """,
            {"account_no": account_no},
        )
        columns = [col[0].lower() for col in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]


def login_account(account_no: int, password: str, config: DatabaseConfig | None = None) -> dict[str, Any]:
    """Authenticate account with password."""
    from unk029_local_package.exceptions import InvalidPasswordError
    with get_cursor(config) as cur:
        cur.execute(
            "SELECT account_no, name, balance, sortcode, password, email FROM accounts WHERE account_no = :id",
            {"id": account_no},
        )
        row = cur.fetchone()
        if not row:
            raise AccountNotFoundError(account_no)
        if row[4] != password:
            raise InvalidPasswordError()
        return {
            "account_no": row[0],
            "name": row[1],
            "balance": row[2],
            "sortcode": row[3],
        }

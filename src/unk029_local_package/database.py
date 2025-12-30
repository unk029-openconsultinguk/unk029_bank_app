"""
Database configuration and connection management for Oracle.
"""

from collections.abc import Generator
from contextlib import contextmanager
import os
from typing import Any

from dotenv import load_dotenv
import oracledb

from .exceptions import AccountNotFoundError, InsufficientFundsError
from .models import AccountCreate, Deposit, LoginRequest, PayeeCreate, Transfer, WithDraw

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
        max_id = cur.fetchone()[0] or 12345000
        account_no = max_id + 1

        # Always use default sortcode and balance
        default_sortcode = "11-11-11"
        default_balance = 1000.0

        # Insert new account
        cur.execute(
            "INSERT INTO accounts (account_no, name, balance, password, sortcode, email) "
            "VALUES (:id, :name, :balance, :password, :sortcode, :email)",
            {
                "id": account_no,
                "name": account.name,
                "balance": default_balance,
                "password": account.password,
                "sortcode": default_sortcode,
                "email": account.email,
            },
        )
        return {
            "account_no": account_no,
            "name": account.name,
            "balance": default_balance,
            "sortcode": default_sortcode,
            "password": account.password,
            "email": account.email,
        }


def deposit_account(
    account_no: int, deposit: Deposit, config: DatabaseConfig | None = None
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
        new_balance = balance + deposit.amount
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
    description: str | None = None,
    related_account_no: int | None = None,
    direction: str | None = None,
    status: str | None = None,
    config: "DatabaseConfig | None" = None,
) -> None:
    """Insert a transaction record."""
    with get_cursor(config) as cur:
        cur.execute(
            (
                "INSERT INTO transactions (from_account, type, amount, description, "
                "to_account, direction, status) "
                "VALUES (:from_account, :type, :amount, :description, "
                ":to_account, :direction, :status)"
            ),
            {
                "from_account": account_no,
                "type": type,
                "amount": amount,
                "description": description,
                "to_account": related_account_no,
                "direction": direction,
                "status": status,
            },
        )


def get_transactions(
    account_no: int, config: DatabaseConfig | None = None
) -> list[dict[str, Any]]:
    """Fetch all transactions for an account, most recent first."""
    with get_cursor(config) as cur:
        cur.execute(
            """
            SELECT 
                id, type, amount, description, created_at, 
                to_account as related_account_no, direction, status
            FROM transactions
            WHERE from_account = :account_no
            ORDER BY created_at DESC
            """,
            {"account_no": account_no},
        )
        description = cur.description or []
        if not description:
            return []
        columns = [col[0].lower() for col in description]
        return [dict(zip(columns, row, strict=False)) for row in cur.fetchall()]


def login_account(login: "LoginRequest", config: DatabaseConfig | None = None) -> dict[str, Any]:
    """Authenticate account with password using account_no or email."""
    from .exceptions import AccountNotFoundError, InvalidPasswordError

    with get_cursor(config) as cur:
        if login.account_no is not None:
            cur.execute(
                (
                    "SELECT account_no, name, balance, sortcode, password, email "
                    "FROM accounts WHERE account_no = :id"
                ),
                {"id": login.account_no},
            )
        elif login.email is not None:
            cur.execute(
                (
                    "SELECT account_no, name, balance, sortcode, password, email "
                    "FROM accounts WHERE email = :email"
                ),
                {"email": login.email},
            )
        else:
            raise AccountNotFoundError(0)
        row = cur.fetchone()
        if not row:
            account_id = login.account_no if login.account_no is not None else 0
            raise AccountNotFoundError(account_id)
        import logging

        logging.basicConfig(level=logging.INFO)
        logging.info(f"DB password: '{row[4]}' | Input password: '{login.password}'")
        if row[4] != login.password:
            raise InvalidPasswordError()
        return {
            "account_no": row[0],
            "name": row[1],
            "balance": row[2],
            "sortcode": row[3],
        }


def add_payee(payee: "PayeeCreate", config: DatabaseConfig | None = None) -> dict[str, Any]:
    """Insert a new payee for a user."""
    with get_cursor(config) as cur:
        cur.execute(
            """
            INSERT INTO payee 
                (user_account_no, payee_name, payee_account_no, payee_sort_code)
            VALUES 
                (:user_account_no, :payee_name, :payee_account_no, :payee_sort_code)
            """,
            {
                "user_account_no": payee.user_account_no,
                "payee_name": payee.payee_name,
                "payee_account_no": payee.payee_account_no,
                "payee_sort_code": payee.payee_sort_code,
            },
        )
        return {
            "user_account_no": payee.user_account_no,
            "payee_name": payee.payee_name,
            "payee_account_no": payee.payee_account_no,
            "payee_sort_code": payee.payee_sort_code,
        }


def list_payees(
    user_account_no: int, config: DatabaseConfig | None = None
) -> list[dict[str, Any]]:
    """List all payees for a user."""
    with get_cursor(config) as cur:
        cur.execute(
            """
            SELECT 
                id, user_account_no, payee_name, payee_account_no, 
                payee_sort_code, created_at 
            FROM payee 
            WHERE user_account_no = :user_account_no 
            ORDER BY created_at DESC
            """,
            {"user_account_no": user_account_no},
        )
        if cur.description is None:
            return []
        columns = [d[0].lower() for d in cur.description]
        return [dict(zip(columns, row, strict=False)) for row in cur.fetchall()]


def update_account(
    account_no: int,
    email: str | None = None,
    mobile: str | None = None,
    password: str | None = None,
    config: DatabaseConfig | None = None,
) -> dict[str, Any]:
    """Update account details (email, mobile, password)."""
    with get_cursor(config) as cur:
        # Build update query dynamically based on provided fields
        updates = []
        params: dict[str, Any] = {"account_no": account_no}

        if email is not None:
            updates.append("email = :email")
            params["email"] = email

        if mobile is not None:
            updates.append("mobile = :mobile")
            params["mobile"] = mobile

        if password is not None:
            updates.append("password = :password")
            params["password"] = password

        if not updates:
            # Nothing to update
            return get_account(account_no, config)

        query = f"UPDATE accounts SET {', '.join(updates)} WHERE account_no = :account_no"
        cur.execute(query, params)

        return get_account(account_no, config)

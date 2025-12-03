"""
FastAPI Server - Core banking API
Handles account management, database connections and banking operations.
"""

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from unk029.database import DatabaseConfig, get_cursor
from unk029.exceptions import AccountNotFoundError, InsufficientFundsError
from unk029.models import AccountCreate, TopUp, WithDraw

app = FastAPI(
    title="UNK029 Bank API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    root_path="/bank",
)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


# ============== Database Operations ==============


def get_account(account_no: int, config: DatabaseConfig | None = None) -> dict[str, Any]:
    """Get account details by account number."""
    with get_cursor(config) as cur:
        cur.execute(
            "SELECT account_no, name, balance FROM accounts WHERE account_no = :id",
            {"id": account_no},
        )
        row = cur.fetchone()
        if row:
            return {"account_no": row[0], "name": row[1], "balance": row[2]}
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
            "INSERT INTO accounts (account_no, name, balance, password) "
            "VALUES (:id, :name, :balance, :password)",
            {
                "id": account_no,
                "name": account.name,
                "balance": account.balance,
                "password": account.password,
            },
        )
        return {"account_no": account_no, "name": account.name, "balance": account.balance}


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


# ============== API Endpoints ==============


@app.get("/account/{account_no}")
def get_account_endpoint(account_no: int) -> dict[str, Any]:
    try:
        return get_account(account_no)
    except AccountNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@app.post("/account")
def create_account_endpoint(account: AccountCreate) -> dict[str, Any]:
    return create_account(account)


@app.patch("/account/{account_no}/topup")
def topup_account_endpoint(account_no: int, topup: TopUp) -> dict[str, Any]:
    try:
        return topup_account(account_no, topup)
    except AccountNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@app.patch("/account/{account_no}/withdraw")
def withdraw_account_endpoint(account_no: int, withdraw: WithDraw) -> dict[str, Any]:
    try:
        return withdraw_account(account_no, withdraw)
    except AccountNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except InsufficientFundsError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)

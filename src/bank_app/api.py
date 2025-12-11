"""
FastAPI Server - Core banking API
Handles account management and banking operations.
"""

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from unk029.database import (
    create_account,
    get_account,
    get_connection,
    topup_account,
    transfer_account,
    withdraw_account,
)
from unk029.exceptions import AccountNotFoundError, InsufficientFundsError
from unk029.models import AccountCreate, TopUp, Transfer, WithDraw


class LoginRequest(BaseModel):
    account_no: int
    password: str


app = FastAPI(
    title="UNK029 Bank API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    root_path="/api",
)


# ============== API Endpoints ==============


@app.post("/account/login", include_in_schema=False)
def login_endpoint(login: LoginRequest) -> dict[str, Any]:
    """Authenticate account with password."""
    try:
        # Query database directly for authentication
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT account_no, name, balance, sortcode, password, email"
            " FROM accounts WHERE account_no = :id",
            {"id": login.account_no},
        )
        row = cur.fetchone()
        cur.close()
        conn.close()

        if not row:
            raise HTTPException(status_code=404, detail="Account not found")

        # Check password (row[4] is password column)
        if row[4] != login.password:
            raise HTTPException(status_code=401, detail="Invalid password")

        return {"account_no": row[0], "name": row[1], "balance": row[2], "sortcode": row[3]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/account/transfer")
def transfer_account_endpoint(transfer: Transfer) -> Any:
    try:
        return transfer_account(transfer)
    except AccountNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except InsufficientFundsError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.get("/account/{account_no}", include_in_schema=False)
def get_account_endpoint(account_no: int) -> Any:
    try:
        return get_account(account_no)
    except AccountNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@app.post("/account/validate", include_in_schema=False)
def validate_account_endpoint(account_no: int, sort_code: str) -> dict[str, Any]:
    """Validate that sort code matches the account number"""
    try:
        account = get_account(account_no)

        # Normalize sort codes for comparison (remove dashes)
        provided_sort_code = sort_code.replace("-", "")
        db_sort_code = account.get("sortcode", "").replace("-", "")

        # Check if sort codes match
        if provided_sort_code != db_sort_code:
            expected = account.get("sortcode")
            raise HTTPException(
                status_code=400,
                detail=f"Sort code does not match this account. Expected: {expected}",
            )

        return {
            "valid": True,
            "account_no": account["account_no"],
            "name": account["name"],
            "sortcode": account["sortcode"],
        }
    except AccountNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@app.post("/account", include_in_schema=False)
def create_account_endpoint(account: AccountCreate) -> Any:
    return create_account(account)


@app.patch("/account/{account_no}/topup", include_in_schema=False)
def topup_account_endpoint(account_no: int, topup: TopUp) -> Any:
    try:
        return topup_account(account_no, topup)
    except AccountNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@app.patch("/account/{account_no}/withdraw", include_in_schema=False)
def withdraw_account_endpoint(account_no: int, withdraw: WithDraw) -> Any:
    try:
        return withdraw_account(account_no, withdraw)
    except AccountNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except InsufficientFundsError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.get("/health")
def health() -> dict[str, str]:
    return {"message": "FastAPI is running"}


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "UNK Bank API", "status": "running", "version": "1.0"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)

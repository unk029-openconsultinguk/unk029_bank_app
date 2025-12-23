"""FastAPI Server - Core banking API
Handles account management and banking operations.
"""

import os
from typing import Any

from fastapi import FastAPI, HTTPException, Header, Request
from pydantic import BaseModel

from unk029.database import (
    create_account,
    get_account,
    get_transactions,
    insert_transaction,
    login_account,
    deposit_account,
    transfer_account,
    withdraw_account,
    add_payee,
    list_payees,
    update_account,
)
from unk029.exceptions import AccountNotFoundError, InsufficientFundsError, InvalidPasswordError
from unk029.models import AccountCreate, Deposit, Transfer, WithDraw, CrossBankTransfer, PayeeCreate, LoginRequest, AccountUpdate


app = FastAPI(
    title="UNK029 Bank API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    root_path="/api",
)


# ============== API Endpoints ==============


@app.post("/account/login", include_in_schema=False)
def login_endpoint(login: LoginRequest) -> Any:
    try:
        return login_account(login)
    except AccountNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except InvalidPasswordError as e:
        raise HTTPException(status_code=401, detail="Invalid password") from e
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e)) from e


@app.post("/account/transfer")
def transfer_account_endpoint(transfer: Transfer, x_logged_in_account: str = Header(None)) -> Any:
    # Validate that the transfer is from the logged-in account
    if not x_logged_in_account:
        raise HTTPException(status_code=401, detail="Authentication required. Please log in first.")
    
    if int(x_logged_in_account) != transfer.from_account_no:
        raise HTTPException(
            status_code=403, 
            detail=f"You can only transfer from your logged-in account ({x_logged_in_account}). Cannot transfer from account {transfer.from_account_no}."
        )
    
    try:
        result = transfer_account(transfer)
        
        # Get account names for friendly descriptions
        from_account = get_account(transfer.from_account_no)
        to_account = get_account(transfer.to_account_no)
        
        # Record transaction for sender (outgoing)
        insert_transaction(
            account_no=transfer.from_account_no,
            type="transfer",
            amount=transfer.amount,
            description=f"Transferred to account {transfer.to_account_no}, {to_account['name']}",
            related_account_no=transfer.to_account_no,
            direction="out",
            status="success",
        )
        
        # Record transaction for receiver (incoming)
        insert_transaction(
            account_no=transfer.to_account_no,
            type="transfer",
            amount=transfer.amount,
            description=f"Transferred from account {transfer.from_account_no}, {from_account['name']}",
            related_account_no=transfer.from_account_no,
            direction="in",
            status="success",
        )
        
        return result
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


@app.put("/account/{account_no}", include_in_schema=False)
def update_account_endpoint(account_no: int, update: AccountUpdate) -> Any:
    """Update account details (email, mobile, password)"""
    try:
        return update_account(
            account_no=account_no,
            email=update.email,
            mobile=update.mobile,
            password=update.password
        )
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


@app.patch("/account/{account_no}/deposit")
def deposit_account_endpoint(account_no: int, deposit: Deposit) -> Any:
    try:
        result = deposit_account(account_no, deposit)
        insert_transaction(
            account_no=account_no,
            type="deposit",
            amount=deposit.amount,
            description=f"Deposited £{deposit.amount}",
            direction="in",
        )
        return result
    except AccountNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@app.patch("/account/{account_no}/withdraw")
def withdraw_account_endpoint(account_no: int, withdraw: WithDraw) -> Any:
    try:
        result = withdraw_account(account_no, withdraw)
        insert_transaction(
            account_no=account_no,
            type="withdraw",
            amount=withdraw.amount,
            description=f"Withdrawn £{withdraw.amount}",
            direction="out",
        )
        return result
    except AccountNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except InsufficientFundsError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.get("/health")
def health() -> dict[str, str]:
    return {"message": "FastAPI is running"}


# ============== Payee API Endpoints ==============

@app.post("/payee", response_model=dict)
def create_payee_endpoint(payee: PayeeCreate):
    try:
        return add_payee(payee)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/payees/{user_account_no}", response_model=list)
def list_payees_endpoint(user_account_no: int):
    try:
        return list_payees(user_account_no)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============== Partner Banks Configuration ==============
# Bank URLs are loaded from environment variables (set in .env file)
URR034_BANK_URL = os.getenv("URR034_BANK_URL", "")
UBF041_BANK_URL = os.getenv("UBF041_BANK_URL", "")
UIA037_BANK_URL = os.getenv("UIA037_BANK_URL", "")
USS016_BANK_URL = os.getenv("USS016_BANK_URL", "")

PARTNER_BANKS = [
    {
        "code": "unk029",
        "name": "UNK Bank (Internal)",
        "url": "/api",
        "isInternal": True,
        "transferMethod": "internal",
        "sort_code": "11-11-11",
    },
    {
        "code": "urr034",
        "name": "Purple Bank",
        "url": URR034_BANK_URL,
        "isInternal": False,
        "transferMethod": "query_params",  # POST /api/deposit/?account_number&amount
        "sort_code": "60-00-01",
    },
    # {
    #     "code": "uia037",
    #     "name": "Secure Bank",
    #     "url": UIA037_BANK_URL,
    #     "isInternal": False,
    #     "transferMethod": "deposit",  # POST /api/deposit with JSON body
    #     "sort_code": "11-22-33",
    # },
    # {
    #     "code": "uss016",
    #     "name": "AppyPay",
    #     "url": USS016_BANK_URL,
    #     "isInternal": False,
    #     "transferMethod": "deposit",  # POST /api/deposit with JSON body
    #     "sort_code": "33-44-55",
    # },
    {
        "code": "ubf041",
        "name": "Bartley Bank",
        "url": UBF041_BANK_URL,
        "isInternal": False,
        "transferMethod": "deposit",  # POST /api/deposit with JSON body
        "sort_code": "20-40-41",
    },
]


@app.get("/banks", include_in_schema=False)
def get_partner_banks() -> list[dict[str, Any]]:
    """Get list of available banks for transfers."""
    return PARTNER_BANKS


@app.post("/account/cross-bank-transfer")
def cross_bank_transfer(transfer: CrossBankTransfer, x_logged_in_account: str = Header(None)) -> Any:
    """Transfer money to another bank's account."""
    import requests  # type: ignore

    # Validate that the transfer is from the logged-in account
    if not x_logged_in_account:
        raise HTTPException(status_code=401, detail="Authentication required. Please log in first.")
    
    if int(x_logged_in_account) != transfer.from_account_no:
        raise HTTPException(
            status_code=403, 
            detail=f"You can only transfer from your logged-in account ({x_logged_in_account}). Cannot transfer from account {transfer.from_account_no}."
        )

    # Find the target bank
    target_bank = next((b for b in PARTNER_BANKS if b["code"] == transfer.to_bank_code), None)
    if not target_bank:
        raise HTTPException(status_code=400, detail=f"Unknown bank: {transfer.to_bank_code}")

    if target_bank.get("isInternal"):
        raise HTTPException(
            status_code=400, detail="Use internal transfer for same-bank transfers"
        )

    # First, withdraw from sender's account
    try:
        withdraw_account(transfer.from_account_no, WithDraw(amount=transfer.amount))
    except AccountNotFoundError as e:
        insert_transaction(
            account_no=transfer.from_account_no,
            type="transfer",
            amount=transfer.amount,
            description=(
                f"Failed transfer to {transfer.to_name}, account {transfer.to_account_no} "
                f"at {target_bank['name']}: Account not found"
            ),
            related_account_no=transfer.to_account_no,
            direction="out",
            status="fail",
        )
        raise HTTPException(status_code=404, detail=str(e)) from e
    except InsufficientFundsError as e:
        insert_transaction(
            account_no=transfer.from_account_no,
            type="transfer",
            amount=transfer.amount,
            description=(
                f"Failed transfer to {transfer.to_name}, account {transfer.to_account_no} "
                f"at {target_bank['name']}: Insufficient funds"
            ),
            related_account_no=transfer.to_account_no,
            direction="out",
            status="fail",
        )
        raise HTTPException(status_code=400, detail=str(e)) from e

    # Then deposit to external bank
    try:
        bank_url = target_bank["url"]
        method = target_bank["transferMethod"]

        if method == "query_params":
            # URR034 (Purple Bank): POST {base_api}/deposit/ with query parameters
            response = requests.post(
                f"{bank_url.rstrip('/')}/deposit/",
                params={
                    "account_number": str(transfer.to_account_no),
                    "amount": transfer.amount,
                },
                timeout=30,
                verify=False,
                allow_redirects=True,
            )
        elif method == "deposit":
            # UBF041 style: POST {base_api}/deposit with JSON body
            response = requests.post(
                f"{bank_url.rstrip('/')}/deposit",
                json={
                    "account_number": str(transfer.to_account_no),
                    "sort_code": transfer.to_sort_code,
                    "account_holder": transfer.to_name,
                    "amount": transfer.amount,
                },
                timeout=30,
            )
        else:
            # Refund on unknown method
            deposit_account(transfer.from_account_no, Deposit(amount=transfer.amount))
            insert_transaction(
                account_no=transfer.from_account_no,
                type="transfer",
                amount=transfer.amount,
                description=f"Failed transfer to {transfer.to_name} at {target_bank['name']}: Unsupported transfer method",
                related_account_no=transfer.to_account_no,
                direction="out",
                status="fail",
            )
            raise HTTPException(status_code=400, detail=f"Unsupported transfer method: {method}")

        if not response.ok:
            # Refund on failure
            deposit_account(transfer.from_account_no, Deposit(amount=transfer.amount))
            error_detail = (
                response.json().get("detail", response.text)
                if response.text
                else "External bank error"
            )
            insert_transaction(
                account_no=transfer.from_account_no,
                type="transfer",
                amount=transfer.amount,
                description=(
                    f"Failed transfer to {transfer.to_name}, account {transfer.to_account_no} "
                    f"at {target_bank['name']}: {error_detail}"
                ),
                related_account_no=transfer.to_account_no,
                direction="out",
                status="fail",
            )
            raise HTTPException(
                status_code=502, detail=f"External bank rejected transfer: {error_detail}"
            )

        # Success
        insert_transaction(
            account_no=transfer.from_account_no,
            type="transfer",
            amount=transfer.amount,
            description=f"Transferred £{transfer.amount} to {transfer.to_name}, account {transfer.to_account_no} at {target_bank['name']}",
            related_account_no=transfer.to_account_no,
            direction="out",
            status="success",
        )

        return {
            "success": True,
            "message": f"Successfully transferred £{transfer.amount:.2f} to {target_bank['name']}",
            "from_account": transfer.from_account_no,
            "to_bank": transfer.to_bank_code,
            "to_account": transfer.to_account_no,
            "amount": transfer.amount,
        }

    except requests.RequestException as e:
        # Refund on network error
        deposit_account(transfer.from_account_no, Deposit(amount=transfer.amount))
        insert_transaction(
            account_no=transfer.from_account_no,
            type="withdraw",
            amount=transfer.amount,
            description=(f"Cross-bank transfer failed: network error {e!s}"),
            related_account_no=transfer.to_account_no,
            direction="out",
            status="fail",
        )
        raise HTTPException(
            status_code=502, detail=f"Failed to connect to external bank: {e!s}"
        ) from e


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "UNK Bank API", "status": "running", "version": "1.0"}


@app.get("/account/{account_no}/transactions")
def get_account_transactions(account_no: int) -> Any:
    try:
        return {"transactions": get_transactions(account_no)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e




if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)

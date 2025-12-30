"""FastAPI Server - Core banking API
Handles account management and banking operations.
"""
import os
from typing import Any
from fastapi import FastAPI, Header, HTTPException
from unk029_local_package.database import (
    add_payee,
    create_account,
    deposit_account,
    get_account,
    get_transactions,
    insert_transaction,
    list_payees,
    login_account,
    transfer_account,
    update_account,
    withdraw_account,
)
from unk029_local_package.banks import (
    get_external_banks,
    get_internal_bank,
    discover_deposit_endpoint,
)
from unk029_local_package.exceptions import AccountNotFoundError, InsufficientFundsError, InvalidPasswordError
from unk029_local_package.models import (
    AccountCreate,
    AccountUpdate,
    Deposit,
    LoginRequest,
    PayeeCreate,
    Transfer,
    UniversalTransfer,
    WithDraw,
)

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


def _validate_sender(from_account_no: int, x_logged_in_account: str | None):
    """Shared validation for account ownership."""
    if not x_logged_in_account:
        raise HTTPException(
            status_code=401, detail="Authentication required. Please log in first."
        )
    if int(x_logged_in_account) != from_account_no:
        raise HTTPException(
            status_code=403,
            detail=f"You can only transfer from your own account ({x_logged_in_account}).",
        )


@app.post("/account/transfer")
def transfer_endpoint(
    transfer: UniversalTransfer, x_logged_in_account: str = Header(None)
) -> Any:
    """Unified endpoint for both internal and external transfers."""
    _validate_sender(transfer.from_account_no, x_logged_in_account)

    internal_bank = get_internal_bank()
    def norm(sc: str | None) -> str:
        return "".join(filter(str.isdigit, sc)) if sc else ""

    target_sc = norm(transfer.to_sort_code)
    internal_sc = norm(internal_bank.get("sort_code"))

    # 1. INTERNAL TRANSFER
    if not target_sc or target_sc == internal_sc:
        try:
            result = transfer_account(Transfer(**transfer.model_dump(exclude={"to_sort_code", "to_name"})))
            from_acc = get_account(transfer.from_account_no)
            to_acc = get_account(transfer.to_account_no)

            insert_transaction(transfer.from_account_no, "transfer", transfer.amount, 
                               f"To {to_acc['name']} (Acc: {transfer.to_account_no})", transfer.to_account_no, "out")
            insert_transaction(transfer.to_account_no, "transfer", transfer.amount, 
                               f"From {from_acc['name']} (Acc: {transfer.from_account_no})", transfer.from_account_no, "in")
            return result
        except (AccountNotFoundError, InsufficientFundsError) as e:
            raise HTTPException(status_code=400 if isinstance(e, InsufficientFundsError) else 404, detail=str(e))

    # 2. EXTERNAL TRANSFER
    target_bank = next((b for b in get_external_banks() if norm(b.get("sort_code")) == target_sc), None)
    if not target_bank:
        raise HTTPException(status_code=400, detail=f"Unknown sort code: {transfer.to_sort_code}")

    return _handle_external_transfer(transfer, target_bank)


def _handle_external_transfer(transfer: UniversalTransfer, target_bank: dict) -> Any:
    import requests
    
    # Withdraw first
    try:
        withdraw_account(transfer.from_account_no, WithDraw(amount=transfer.amount))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        bank_url = target_bank["url"].rstrip("/")
        endpoint, method = discover_deposit_endpoint(bank_url)
        
        # Replace path params
        for key in ["{account_id}", "{account_number}", "{id}", "{accountNo}"]:
            endpoint = endpoint.replace(key, str(transfer.to_account_no))
            
        full_url = f"{bank_url}{endpoint}"
        payload = {
            "account_number": str(transfer.to_account_no),
            "sort_code": transfer.to_sort_code,
            "account_holder": transfer.to_name,
            "amount": transfer.amount,
            "description": f"Transfer from {get_internal_bank()['name']}",
            "from_account_number": str(transfer.from_account_no),
            "from_sort_code": get_internal_bank()["sort_code"],
        }

        if target_bank.get("transferMethod") == "query_params":
            resp = requests.post(full_url, params={"account_number": transfer.to_account_no, "amount": transfer.amount}, timeout=30, verify=False)
        else:
            resp = requests.request(method, full_url, json=payload, timeout=30, verify=False)

        if not resp.ok:
            raise Exception(resp.json().get("detail", resp.text))

        insert_transaction(transfer.from_account_no, "transfer", transfer.amount, 
                           f"To {transfer.to_name} at {target_bank['name']}", transfer.to_account_no, "out", "success")
        return f"Successfully transferred £{transfer.amount:.2f} to {target_bank['name']}"

    except Exception as e:
        deposit_account(transfer.from_account_no, Deposit(amount=transfer.amount)) # Refund
        insert_transaction(transfer.from_account_no, "transfer", transfer.amount, f"Failed to {target_bank['name']}: {str(e)}"[:255], status="fail")
        raise HTTPException(status_code=502, detail=f"External bank error: {str(e)}")


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
            password=update.password,
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

@app.get("/banks", include_in_schema=False)
def get_partner_banks() -> list[dict[str, Any]]:
    """Get list of available banks for transfers."""
    return [get_internal_bank()] + get_external_banks()


@app.get("/account/{account_no}/transactions")
def get_account_transactions(account_no: int) -> Any:
    try:
        return {"transactions": get_transactions(account_no)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/health")
def health() -> dict[str, str]:
    return {"message": "FastAPI is running"}


# ============== Payee API Endpoints ==============


@app.post("/payee", response_model=dict)
def create_payee_endpoint(payee: PayeeCreate) -> dict[str, Any]:
    try:
        return add_payee(payee)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.get("/payees/{user_account_no}", response_model=list)
def list_payees_endpoint(user_account_no: int) -> list[dict[str, Any]]:
    try:
        return list_payees(user_account_no)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
        

@app.get("/")
def root() -> dict[str, str]:
    return {"service": "UNK Bank API", "status": "running", "version": "1.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

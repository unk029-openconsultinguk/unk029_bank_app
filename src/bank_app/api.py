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
    topup_account,
    transfer_account,
    withdraw_account,
)
from unk029.exceptions import AccountNotFoundError, InsufficientFundsError
from unk029.models import AccountCreate, TopUp, Transfer, WithDraw

app = FastAPI(
    title="UNK029 Bank API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


# ============== API Endpoints ==============
@app.post("/account/transfer")
def transfer_account_endpoint(transfer: Transfer) -> dict[str, Any]:
    try:
        return transfer_account(transfer)
    except AccountNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except InsufficientFundsError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.get("/account/{account_no}", include_in_schema=False)
def get_account_endpoint(account_no: int) -> dict[str, Any]:
    try:
        return get_account(account_no)
    except AccountNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@app.post("/account", include_in_schema=False)
def create_account_endpoint(account: AccountCreate) -> dict[str, Any]:
    return create_account(account)


@app.patch("/account/{account_no}/topup", include_in_schema=False)
def topup_account_endpoint(account_no: int, topup: TopUp) -> dict[str, Any]:
    try:
        return topup_account(account_no, topup)
    except AccountNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@app.patch("/account/{account_no}/withdraw", include_in_schema=False)
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

"""
FastAPI Server - Core banking API
Handles account management and banking operations.
"""

from typing import Any
import httpx
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
from bank_app.bank_agent.agent import root_agent


class ChatRequest(BaseModel):
    message: str
    account_no: int | None = None


class ChatResponse(BaseModel):
    response: str
    account_no: int | None = None

app = FastAPI(
    title="UNK029 Bank API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


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


@app.post("/account/validate", include_in_schema=False)
def validate_account_endpoint(account_no: int, sort_code: str) -> dict[str, Any]:
    """Validate that sort code matches the account number"""
    try:
        account = get_account(account_no)
        
        # Normalize sort codes for comparison (remove dashes)
        provided_sort_code = sort_code.replace('-', '')
        db_sort_code = account.get('sortcode', '').replace('-', '')
        
        # Check if sort codes match
        if provided_sort_code != db_sort_code:
            raise HTTPException(
                status_code=400, 
                detail=f"Sort code does not match this account. Expected: {account.get('sortcode')}"
            )
        
        return {
            "valid": True,
            "account_no": account["account_no"],
            "name": account["name"],
            "sortcode": account["sortcode"]
        }
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


@app.get("/health")
def health() -> dict[str, str]:
    return {"message": "FastAPI is running"}


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "message": "UNK029 Bank API is running",
        "version": "1.0",
        "architecture": {
            "web_ui": "React Frontend → FastAPI → Oracle DB",
            "ai_chat": "Frontend Chat → Google ADK Agent → MCP Server → FastAPI → Oracle DB"
        },
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "chat": "/api/chat",
            "account": "/api/account/{account_no}",
            "dev_ui": "/dev-ui/"
        }
    }


@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """Chat with the AI banking assistant powered by Google ADK Agent and MCP Tools"""
    try:
        import asyncio
        from google.adk.agents import InvocationContext
        
        # Add account context to the message if available
        context_message = request.message
        if request.account_no:
            context_message = f"[Account: {request.account_no}] {request.message}"
        
        # Create invocation context with user message
        context = InvocationContext(
            session_id="web_session",
            user_content=context_message
        )
        
        # Call the Google ADK Agent using run_async
        response_text = ""
        async for event in root_agent.run_async(parent_context=context):
            # Collect text from response events
            if hasattr(event, 'text') and event.text:
                response_text += event.text
            elif hasattr(event, 'content') and event.content:
                response_text += str(event.content)
        
        if not response_text:
            response_text = "I processed your request but didn't generate a response."
        
        return ChatResponse(
            response=response_text.strip(),
            account_no=request.account_no
        )
    except Exception as e:
        # Log the error and return to user
        import traceback
        print(f"Chat error: {str(e)}")
        print(traceback.format_exc())
        return ChatResponse(
            response=f"❌ Sorry, I encountered an error. Please try again.",
            account_no=request.account_no
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)

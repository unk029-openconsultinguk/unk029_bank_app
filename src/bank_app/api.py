"""
FastAPI Server - Core banking API
Handles account management and banking operations.
"""

from typing import Any
import httpx
import os
import asyncio
import json
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
from bank_app.bank_agent import root_agent

app = FastAPI(
    title="UNK029 Bank API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


class ChatRequest(BaseModel):
    message: str
    account_number: str = None
    use_tools: bool = False


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


def _extract_text_from_chunk(chunk: Any) -> str:
    """Extract text from various chunk types returned by the agent."""
    if chunk is None:
        return ""
    
    # If it's already a string, return it
    if isinstance(chunk, str):
        return chunk
    
    # Try to get text attribute
    if hasattr(chunk, 'text') and isinstance(chunk.text, str):
        return chunk.text
    
    # Try to get content attribute
    if hasattr(chunk, 'content') and isinstance(chunk.content, str):
        return chunk.content
    
    # Try to convert to string
    try:
        chunk_str = str(chunk).strip()
        # Filter out noise like '<' or empty strings
        if chunk_str and chunk_str not in ['<', '', 'None']:
            return chunk_str
    except:
        pass
    
    return ""


# Chat endpoint - call AI agent directly
@app.post("/api/chat", response_model=ChatResponse, include_in_schema=False)
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """Process chat requests with the AI agent"""
    try:
        response_text = ""
        
        try:
            # Collect all chunks from the async generator
            chunks = []
            async for chunk in root_agent.run_live(request.message):
                chunks.append(chunk)
            
            # Process collected chunks to build response
            for chunk in chunks:
                text = _extract_text_from_chunk(chunk)
                if text:
                    response_text += text
                    
        except AttributeError as attr_error:
            # Handle model_copy and other attribute errors gracefully
            error_msg = str(attr_error)
            print(f"Agent attribute error: {error_msg}")
            # Don't fail silently - still try to return useful response
            if not response_text:
                response_text = "I processed your request but encountered a technical issue. The operation may have been completed. Please check your account."
                
        except Exception as inner_error:
            # If anything else fails
            print(f"Async iteration error: {str(inner_error)}")
            print(f"Error type: {type(inner_error).__name__}")
            if not response_text:
                response_text = f"I encountered an issue processing your request: {str(inner_error)}"
        
        # Ensure we have a response
        if not response_text or response_text.isspace():
            response_text = "I received your message but could not process it properly. Please try again."
        
        return ChatResponse(reply=response_text.strip())
        
    except Exception as e:
        print(f"Chat endpoint error: {str(e)}")
        import traceback
        traceback.print_exc()
        return ChatResponse(reply=f"I apologize, I encountered an error: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)

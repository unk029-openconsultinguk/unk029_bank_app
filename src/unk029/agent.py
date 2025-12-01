"""
AI Agent - Gemini AI with MCP Tool Integration
Uses MCP tools from MCP server to process banking queries.
"""

from fastapi import FastAPI, Request
from pydantic import BaseModel
import google.generativeai as genai
import os
from dotenv import load_dotenv
import re
import json
from functools import lru_cache
from datetime import datetime, timedelta

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

app = FastAPI(title="UNK029 AI Agent - Gemini")

# Request/Response models
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str


# Session state for conversational memory
session_state = {}

# Simple response cache with TTL (Time To Live)
response_cache = {}
CACHE_TTL = 300  # 5 minutes

def get_cached_response(message: str) -> str | None:
    """Get cached response if available and not expired."""
    cache_key = message.lower().strip()
    if cache_key in response_cache:
        cached, timestamp = response_cache[cache_key]
        if datetime.now() - timestamp < timedelta(seconds=CACHE_TTL):
            print(f"DEBUG: Cache hit for: {message[:50]}", flush=True)
            return cached
        else:
            del response_cache[cache_key]
    return None

def cache_response(message: str, response: str) -> None:
    """Cache response with current timestamp."""
    cache_key = message.lower().strip()
    response_cache[cache_key] = (response, datetime.now())
    # Clean old entries if cache gets too large
    if len(response_cache) > 100:
        oldest_key = min(response_cache.keys(), key=lambda k: response_cache[k][1])
        del response_cache[oldest_key]

def _get_session_key(request: Request) -> str:
    """Get session key from client IP (use real session ID in production)."""
    return request.client.host if request and request.client else "default"


# MCP Tool Integration - Uses MCP Server HTTP Endpoint
def call_mcp_tool(tool_name: str, **kwargs) -> dict:
    """
    Call banking tools via MCP Server HTTP.
    MCP Server exposes FastAPI endpoints for banking operations.
    Agent calls these endpoints through the MCP abstraction layer.
    
    Args:
        tool_name: Name of the MCP tool (e.g., 'get_account_tool')
        **kwargs: Tool parameters
        
    Returns:
        Response (success/error format)
    """
    import httpx
    
    try:
        with httpx.Client(timeout=5.0) as client:
            # Call MCP Server (port 8002) which wraps FastAPI endpoints
            mcp_url = "http://unk029_mcp_server:8002"
            
            print(f"DEBUG: Calling MCP tool: {tool_name} with params: {kwargs}", flush=True)
            
            if tool_name == "get_account_tool":
                account_no = kwargs.get("account_no")
                response = client.get(f"{mcp_url}/account/{account_no}")
                if response.status_code == 200:
                    account = response.json()
                    return {"success": True, "data": account}
                else:
                    return {"success": False, "error": "Account not found"}
                    
            elif tool_name == "topup_account_tool":
                account_no = kwargs.get("account_no")
                amount = kwargs.get("amount")
                response = client.patch(
                    f"{mcp_url}/account/{account_no}/topup",
                    json={"amount": float(amount)}
                )
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "data": {
                            "name": result.get("name"),
                            "account_no": result.get("account_no"),
                            "amount_deposited": float(amount),
                            "new_balance": result.get("new_balance")
                        }
                    }
                else:
                    error_data = response.json() if response.headers.get("content-type") == "application/json" else {}
                    return {"success": False, "error": error_data.get("detail", "Failed to process deposit")}
                    
            elif tool_name == "withdraw_account_tool":
                account_no = kwargs.get("account_no")
                amount = kwargs.get("amount")
                response = client.patch(
                    f"{mcp_url}/account/{account_no}/withdraw",
                    json={"amount": float(amount)}
                )
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "success": True,
                        "data": {
                            "name": result.get("name"),
                            "account_no": result.get("account_no"),
                            "amount_withdrawn": float(amount),
                            "new_balance": result.get("new_balance")
                        }
                    }
                else:
                    error_data = response.json() if response.headers.get("content-type") == "application/json" else {}
                    return {"success": False, "error": error_data.get("detail", "Failed to process withdrawal")}
            
            return {"success": False, "error": "Unknown tool"}
    except Exception as e:
        print(f"MCP tool call error: {e}", flush=True)
        return {"success": False, "error": f"Failed to call MCP tool: {str(e)}"}


# AI Chat Implementation
async def process_chat(message: str, request: Request = None) -> str:
    """
    Process user message with Gemini AI, using banking API tools.
    
    Args:
        message: User message
        request: FastAPI request object for session management
        
    Returns:
        AI response
    """
    message_lower = message.lower().strip()
    
    # Check cache first (only for general queries without account/amount info)
    cached = get_cached_response(message)
    if cached:
        return cached
    
    # Extract account number and amounts
    account_numbers = re.findall(r'\baccount\s*#?\s*(\d+)\b', message_lower)
    just_number = re.fullmatch(r"\d+", message_lower)
    if just_number:
        account_numbers = [message_lower]
    
    # Extract amounts
    amounts = re.findall(r'[£$]\s*(\d+(?:\.\d{2})?)', message_lower)
    if not amounts:
        withdraw_pattern = r'(?:withdraw|withdrawal|take out)\s+[£$]?(\d+(?:\.\d{2})?)'
        deposit_pattern = r'(?:deposit|add|top\s*up|topup|put in)\s+[£$]?(\d+(?:\.\d{2})?)'
        amounts = re.findall(withdraw_pattern, message_lower) or re.findall(deposit_pattern, message_lower)
    
    print(f"DEBUG: Message: {message}", flush=True)
    print(f"DEBUG: Accounts: {account_numbers}, Amounts: {amounts}", flush=True)
    
    # Keyword detection
    deposit_keywords = ['deposit', 'add', 'top up', 'topup', 'put in', 'credit']
    withdraw_keywords = ['withdraw', 'withdrawal', 'take out', 'debit', 'remove']
    balance_keywords = ['balance', 'how much', 'check account', 'current balance', 'funds', 'money']
    
    is_deposit = any(keyword in message_lower for keyword in deposit_keywords)
    is_withdraw = any(keyword in message_lower for keyword in withdraw_keywords)
    is_balance = any(keyword in message_lower for keyword in balance_keywords)
    
    # Session state management
    session_key = _get_session_key(request) if request else None
    state = session_state.get(session_key, {}) if session_key else {}
    
    # Handle pending intent (user provided additional info after being asked)
    if state.get("pending_intent"):
        pending = state["pending_intent"]
        
        # Balance check pending - user provided account number
        if pending["type"] == "balance" and just_number:
            account_no = int(message_lower)
            result = call_mcp_tool("get_account_tool", account_no=account_no)
            if session_key:
                session_state.pop(session_key, None)
            if result.get("success"):
                data = result["data"]
                return f"Hello {data['name']}! 👋\n\nYour account #{data['account_no']} has a current balance of **£{data['balance']:,.2f}**.\n\nWould you like to make a deposit or withdrawal?"
            else:
                return f"❌ {result.get('error', 'Account not found')}"
        
        # Deposit pending - user provided amount
        elif pending["type"] == "deposit_info_needed" and amounts:
            amount = float(amounts[0])
            account_no = pending.get("account_no")
            if account_no:
                # We have both amount and account, process deposit
                result = call_mcp_tool("topup_account_tool", account_no=account_no, amount=amount)
                if session_key:
                    session_state.pop(session_key, None)
                if result.get("success"):
                    data = result["data"]
                    return f"✅ **Deposit Successful!**\n\nHello {data['name']}! I've deposited **£{data['amount_deposited']:,.2f}** into account #{data['account_no']}.\n\n💰 New Balance: **£{data['new_balance']:,.2f}**\n\nIs there anything else I can help you with?"
                else:
                    return f"❌ {result.get('error', 'Failed to process deposit')}"
            else:
                # Still need account number
                pending["amount"] = amount
                return f"Great! I'll deposit **£{amount:,.2f}**. 💰\n\nNow please provide your account number.\n\nExample: 'Account 1'"
        
        # Withdraw pending - user provided amount
        elif pending["type"] == "withdraw_info_needed" and amounts:
            amount = float(amounts[0])
            account_no = pending.get("account_no")
            if account_no:
                # We have both amount and account, process withdrawal
                result = call_mcp_tool("withdraw_account_tool", account_no=account_no, amount=amount)
                if session_key:
                    session_state.pop(session_key, None)
                if result.get("success"):
                    data = result["data"]
                    return f"✅ **Withdrawal Successful!**\n\nHello {data['name']}! I've withdrawn **£{data['amount_withdrawn']:,.2f}** from account #{data['account_no']}.\n\n💰 New Balance: **£{data['new_balance']:,.2f}**\n\nIs there anything else I can help you with?"
                else:
                    return f"❌ {result.get('error', 'Failed to process withdrawal')}"
            else:
                # Still need account number
                pending["amount"] = amount
                return f"Great! I'll withdraw **£{amount:,.2f}**. 💰\n\nNow please provide your account number.\n\nExample: 'Account 1'"
        
        # Deposit/withdraw pending - user provided account number
        elif (pending["type"] in ["deposit_info_needed", "withdraw_info_needed"]) and just_number:
            account_no = int(message_lower)
            pending["account_no"] = account_no
            action = "deposit" if pending["type"] == "deposit_info_needed" else "withdraw"
            amount = pending.get("amount")
            if amount:
                # We have both amount and account, process it
                if pending["type"] == "deposit_info_needed":
                    result = call_mcp_tool("topup_account_tool", account_no=account_no, amount=amount)
                else:
                    result = call_mcp_tool("withdraw_account_tool", account_no=account_no, amount=amount)
                if session_key:
                    session_state.pop(session_key, None)
                if result.get("success"):
                    data = result["data"]
                    if pending["type"] == "deposit_info_needed":
                        return f"✅ **Deposit Successful!**\n\nHello {data['name']}! I've deposited **£{data['amount_deposited']:,.2f}** into account #{data['account_no']}.\n\n💰 New Balance: **£{data['new_balance']:,.2f}**\n\nIs there anything else I can help you with?"
                    else:
                        return f"✅ **Withdrawal Successful!**\n\nHello {data['name']}! I've withdrawn **£{data['amount_withdrawn']:,.2f}** from account #{data['account_no']}.\n\n💰 New Balance: **£{data['new_balance']:,.2f}**\n\nIs there anything else I can help you with?"
                else:
                    return f"❌ {result.get('error', f'Failed to process {action}')}"
            else:
                # Still need amount
                return f"Perfect! Account #{account_no}. 💰\n\nNow please tell me how much you'd like to {action}.\n\nExample: '£100' or '100'"
    
    # Store pending intent for balance queries without account
    if is_balance and not account_numbers:
        if session_key:
            session_state[session_key] = {"pending_intent": {"type": "balance"}}
        return "I'd be happy to help you check your balance! 💰\n\nPlease provide your account number.\n\nExample: 'What's the balance for account 1?'"
    
    # Store pending intent for deposit/withdraw without any info
    if is_deposit and not account_numbers and not amounts:
        if session_key:
            session_state[session_key] = {"pending_intent": {"type": "deposit_info_needed", "account_no": None, "amount": None}}
        return "I can help you with a deposit! 💰\n\nPlease provide the amount and account number.\n\nExample: '£200 to account 1' or just say the amount first (e.g., '200')"
    
    if is_withdraw and not account_numbers and not amounts:
        if session_key:
            session_state[session_key] = {"pending_intent": {"type": "withdraw_info_needed", "account_no": None, "amount": None}}
        return "I can help you with a withdrawal! 💰\n\nPlease provide the amount and account number.\n\nExample: '£200 from account 1' or just say the amount first (e.g., '200')"
    
    # Handle deposits
    if is_deposit and account_numbers and amounts:
        account_no = int(account_numbers[0])
        amount = float(amounts[0])
        
        result = call_mcp_tool("topup_account_tool", account_no=account_no, amount=amount)
        if result.get("success"):
            data = result["data"]
            return f"✅ **Deposit Successful!**\n\nHello {data['name']}! I've deposited **£{data['amount_deposited']:,.2f}** into account #{data['account_no']}.\n\n💰 New Balance: **£{data['new_balance']:,.2f}**\n\nIs there anything else I can help you with?"
        else:
            return f"❌ {result.get('error', 'Failed to process deposit')}"
    
    # Handle withdrawals
    elif is_withdraw and account_numbers and amounts:
        account_no = int(account_numbers[0])
        amount = float(amounts[0])
        
        result = call_mcp_tool("withdraw_account_tool", account_no=account_no, amount=amount)
        if result.get("success"):
            data = result["data"]
            return f"✅ **Withdrawal Successful!**\n\nHello {data['name']}! I've withdrawn **£{data['amount_withdrawn']:,.2f}** from account #{data['account_no']}.\n\n💰 New Balance: **£{data['new_balance']:,.2f}**\n\nIs there anything else I can help you with?"
        else:
            return f"❌ {result.get('error', 'Failed to process withdrawal')}"
    
    # Handle transactions without account number
    elif (is_deposit or is_withdraw) and amounts:
        action = "deposit" if is_deposit else "withdraw"
        amount = float(amounts[0])
        pending_type = "deposit_info_needed" if is_deposit else "withdraw_info_needed"
        if session_key:
            session_state[session_key] = {"pending_intent": {"type": pending_type, "account_no": None, "amount": amount}}
        return f"Great! I'll {action} **£{amount:,.2f}**. 💰\n\nNow please provide your account number.\n\nExample: 'Account 1' or just say '1'"
    
    # Handle transactions without amount
    elif (is_deposit or is_withdraw) and account_numbers:
        action = "deposit" if is_deposit else "withdraw"
        account_no = int(account_numbers[0])
        pending_type = "deposit_info_needed" if is_deposit else "withdraw_info_needed"
        if session_key:
            session_state[session_key] = {"pending_intent": {"type": pending_type, "account_no": account_no, "amount": None}}
        return f"Perfect! Account #{account_no}. 💰\n\nHow much would you like to {action}?\n\nExample: '£100' or just '100'"
    
    # Handle balance queries with account
    elif is_balance and account_numbers:
        account_no = int(account_numbers[0])
        result = call_mcp_tool("get_account_tool", account_no=account_no)
        if session_key:
            session_state.pop(session_key, None)
        
        if result.get("success"):
            data = result["data"]
            return f"Hello {data['name']}! 👋\n\nYour account #{data['account_no']} has a current balance of **£{data['balance']:,.2f}**.\n\nWould you like to make a deposit or withdrawal?"
        else:
            return f"❌ {result.get('error', 'Account not found')}"
    
    # General banking query - use Gemini with improved prompt
    bank_prompt = f"""You are a friendly banking assistant. Answer in 1-2 sentences.

User: {message}

Banking info: We offer account balance checks, deposits, and withdrawals."""
    
    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(
            bank_prompt,
            generation_config={
                "temperature": 0.5,
                "top_p": 0.9,
                "max_output_tokens": 100,
            },
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
            ]
        )
        
        # Handle Gemini response safely
        result = ""
        if hasattr(response, 'text') and response.text:
            result = response.text.strip()
        elif hasattr(response, 'candidates') and response.candidates:
            for candidate in response.candidates:
                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                    for part in candidate.content.parts:
                        if hasattr(part, 'text') and part.text:
                            result += part.text.strip()
        
        # Fallback if response is empty
        if not result or len(result) < 5:
            result = "Hello! I'm your banking assistant. Ask me about balances, deposits, or withdrawals with your account number."
        
        cache_response(message, result)
        return result
    except Exception as e:
        print(f"Gemini error: {e}", flush=True)
        fallback = "Hello! Ask me about your account balance, deposits, or withdrawals. (Please provide account number)"
        cache_response(message, fallback)
        return fallback


# Endpoint: Chat
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat: ChatRequest, request: Request):
    """Main chat endpoint - process user message via AI with MCP tool integration."""
    print(f"=== AI AGENT CHAT ENDPOINT ===", flush=True)
    print(f"Message: {chat.message}", flush=True)
    reply = await process_chat(chat.message, request)
    print(f"Reply: {reply[:100]}...", flush=True)
    return ChatResponse(reply=reply)


# Health check
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "AI Agent"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)

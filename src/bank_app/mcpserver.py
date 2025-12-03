"""
MCP Server - Banking Transaction Tools
Uses FastAPI with FastMCP integration.
Integrates Google ADK (Agentic Development Kit) for natural language banking interactions.

Architecture:
- FastAPI provides REST endpoints
- FastMCP exposes banking tools
- Google ADK (Gemini AI) calls MCP tools for natural language banking
"""

from collections import defaultdict
from datetime import datetime, timedelta
import logging
import os
import traceback

from fastapi import FastAPI, HTTPException, Request
from fastmcp import FastMCP
from google import genai
from google.genai import types
import httpx
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="UNK029 Bank MCP Server")

# Initialize FastMCP
mcp = FastMCP("UNK029 Bank MCP")

# Initialize Google ADK Client
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable not set")

# Create Google ADK client
client = genai.Client(api_key=GOOGLE_API_KEY)

# Bank API base URL
BANK_API_URL = os.getenv("BANK_API_URL", "http://unk029_bank_app:8001")

# Session management
conversation_sessions: dict[str, list] = defaultdict(list)
SESSION_TIMEOUT = timedelta(minutes=30)
last_activity: dict[str, datetime] = {}

# System instruction for AI assistant
SYSTEM_INSTRUCTION = """You are UNK029 Bank's AI assistant. Be friendly, \
use customer names when known, keep responses concise.

AVAILABLE TOOLS:
1. get_account_tool(account_no): Check balance/account info
2. topup_account_tool(account_no, amount): Deposit money
3. withdraw_account_tool(account_no, amount): Withdraw money  
4. get_banking_info_tool(query_type): Get general banking information \
(interest_rates, fees, limits, services, hours, security, opening_account, \
contact, international, mortgage)

CRITICAL RULES:
1. REMEMBER CONTEXT: If user mentioned an account number earlier, \
use it for follow-up requests like "deposit £200" or "withdraw £50"
2. Use customer's name from previous tool results \
(e.g., if get_account_tool returned name "John", greet them as John)
3. Execute tools immediately when you have the required info
4. Currency is always GBP (£)
5. For general banking questions, use get_banking_info_tool with appropriate query_type

CONTEXT HANDLING:
- "deposit £200" after checking account 2 → use topup_account_tool(2, 200)
- "withdraw £50" after checking account 2 → use withdraw_account_tool(2, 50)
- "what's my balance" after deposit to account 2 → use get_account_tool(2)"""

# Tool definitions (single source of truth)
TOOL_DEFINITIONS = {
    "get_account_tool": {
        "description": "Get account info (balance, name). "
        "Use when user asks about balance or account.",
        "parameters": {"account_no": ("integer", "The account number")},
        "required": ["account_no"],
    },
    "topup_account_tool": {
        "description": "Deposit money into an account.",
        "parameters": {
            "account_no": ("integer", "The account number"),
            "amount": ("number", "Amount to deposit in GBP"),
        },
        "required": ["account_no", "amount"],
    },
    "withdraw_account_tool": {
        "description": "Withdraw money from an account.",
        "parameters": {
            "account_no": ("integer", "The account number"),
            "amount": ("number", "Amount to withdraw in GBP"),
        },
        "required": ["account_no", "amount"],
    },
    "get_banking_info_tool": {
        "description": "Get general banking info (interest_rates, fees, limits, "
        "services, hours, security, opening_account, contact, international, mortgage).",
        "parameters": {"query_type": ("string", "Type of info requested")},
        "required": ["query_type"],
    },
}


def _build_function_declaration(name: str, defn: dict) -> types.FunctionDeclaration:
    """Build a FunctionDeclaration from tool definition."""
    properties = {k: {"type": v[0], "description": v[1]} for k, v in defn["parameters"].items()}
    return types.FunctionDeclaration(
        name=name,
        description=defn["description"],
        parameters={"type": "object", "properties": properties, "required": defn["required"]},
    )


# Generate tool declarations for Google ADK
BANKING_TOOLS = [
    types.Tool(
        function_declarations=[
            _build_function_declaration(name, defn) for name, defn in TOOL_DEFINITIONS.items()
        ]
    )
]

# Log available tools at startup
print(f"[STARTUP] Available tools: {list(TOOL_DEFINITIONS.keys())}")


# Request models
class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


# Helper functions
def get_session_id(request: Request) -> str:
    """Get session ID from request."""
    if request and request.client:
        return request.client.host
    return "default"


def cleanup_old_sessions():
    """Remove expired sessions."""
    now = datetime.now()
    expired = [sid for sid, last in last_activity.items() if now - last > SESSION_TIMEOUT]
    for sid in expired:
        conversation_sessions.pop(sid, None)
        last_activity.pop(sid, None)


# Reusable HTTP client for Bank API calls
def call_bank_api(method: str, endpoint: str, json_data: dict | None = None) -> dict:
    """Make a call to the Bank API."""
    url = f"{BANK_API_URL}{endpoint}"
    try:
        with httpx.Client(timeout=5.0) as http_client:
            if method == "GET":
                response = http_client.get(url)
            elif method == "PATCH":
                response = http_client.patch(url, json=json_data)
            else:
                return {"success": False, "error": f"Unsupported method: {method}"}

            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                is_json = response.headers.get("content-type", "").startswith("application/json")
                error_msg = (
                    response.json().get("detail", "Request failed")
                    if is_json
                    else "Request failed"
                )
                return {"success": False, "error": error_msg}
    except httpx.TimeoutException:
        return {"success": False, "error": "Bank API timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# Banking information data (static, defined before MCP tools that use it)
BANKING_INFO = {
    "interest_rates": {
        "savings_account": "3.5% AER",
        "current_account": "0.1% AER",
        "premium_savings": "4.2% AER (min £10,000)",
        "fixed_term_1year": "4.8% AER",
        "fixed_term_2year": "5.0% AER",
        "overdraft": "19.9% EAR",
        "personal_loan": "6.9% - 29.9% APR (based on credit score)",
        "last_updated": "December 2025",
    },
    "fees": {
        "account_maintenance": "Free for all accounts",
        "atm_withdrawal_uk": "Free at all UK ATMs",
        "atm_withdrawal_international": "£1.50 + 2.75% conversion",
        "bank_transfer_uk": "Free (Faster Payments)",
        "international_transfer": "£5 - £25",
        "failed_payment": "£10 per failed Direct Debit",
        "replacement_card": "Free (standard), £10 (express)",
    },
    "limits": {
        "daily_atm_withdrawal": "£500",
        "daily_card_spending": "£10,000",
        "single_transfer": "£25,000",
        "daily_transfer": "£50,000",
        "contactless": "£100 per transaction",
        "overdraft": "Up to £5,000 (subject to approval)",
    },
    "services": {
        "accounts": ["Current", "Savings", "Premium Savings", "Joint", "Business"],
        "cards": ["Visa Debit", "Mastercard Credit", "Premium Metal"],
        "digital": ["Mobile App", "Online Banking", "AI Assistant", "Apple Pay", "Google Pay"],
        "support": ["24/7 AI", "Phone Support", "In-branch", "Video Banking"],
    },
    "hours": {
        "online_banking": "24/7",
        "ai_assistant": "24/7",
        "phone_support": "8am-10pm (Mon-Fri), 9am-6pm (Sat-Sun)",
        "branches": "9am-5pm (Mon-Fri), 9am-1pm (Sat)",
        "emergency": "24/7",
    },
    "security": {
        "encryption": "256-bit SSL",
        "authentication": "2FA mandatory",
        "biometrics": "Fingerprint & Face ID",
        "fraud_protection": "24/7 monitoring",
        "fscs_protection": "Up to £85,000",
    },
    "opening_account": {
        "requirements": ["UK photo ID", "Proof of address", "UK phone", "Email"],
        "eligibility": "UK resident, 18+",
        "time_to_open": "5-10 minutes online",
        "card_delivery": "3-5 working days",
    },
    "contact": {
        "customer_service": "0800 123 4567",
        "lost_card": "0800 123 4568 (24/7)",
        "fraud": "0800 123 4569 (24/7)",
        "email": "support@unk029bank.com",
    },
    "international": {
        "currencies": "150+",
        "exchange_rate": "Mid-market, no markup",
        "transfer_time": "1-3 business days",
        "receiving": "Free",
    },
    "mortgage": {
        "status": "Coming Q2 2026",
        "types": ["Fixed Rate", "Tracker", "Offset", "Buy-to-Let"],
        "register": "mortgage@unk029bank.com",
    },
}

# Query type aliases for flexible matching
QUERY_ALIASES = {
    "rate": "interest_rates",
    "rates": "interest_rates",
    "interest": "interest_rates",
    "fee": "fees",
    "charges": "fees",
    "cost": "fees",
    "limit": "limits",
    "maximum": "limits",
    "service": "services",
    "product": "services",
    "products": "services",
    "hour": "hours",
    "time": "hours",
    "open": "hours",
    "opening": "hours",
    "secure": "security",
    "safety": "security",
    "protection": "security",
    "phone": "contact",
    "email": "contact",
    "call": "contact",
    "open_account": "opening_account",
    "new_account": "opening_account",
    "create_account": "opening_account",
    "requirements": "opening_account",
    "abroad": "international",
    "foreign": "international",
    "overseas": "international",
    "currency": "international",
    "home_loan": "mortgage",
    "house": "mortgage",
}


# Core banking functions (business logic)
def _get_account(account_no: int) -> dict:
    """Get account information."""
    result = call_bank_api("GET", f"/account/{account_no}")
    if result["success"]:
        data = result["data"]
        return {
            "success": True,
            "data": {
                "account_no": data.get("account_no"),
                "name": data.get("name"),
                "balance": data.get("balance"),
                "currency": "GBP",
            },
        }
    return {"success": False, "error": result.get("error", f"Account #{account_no} not found")}


def _topup_account(account_no: int, amount: float) -> dict:
    """Deposit funds into an account."""
    result = call_bank_api("PATCH", f"/account/{account_no}/topup", {"amount": float(amount)})
    if result["success"]:
        data = result["data"]
        return {
            "success": True,
            "data": {
                "account_no": account_no,
                "name": data.get("name"),
                "amount_deposited": amount,
                "new_balance": data.get("new_balance", data.get("balance")),
                "currency": "GBP",
            },
        }
    return {"success": False, "error": result.get("error", "Failed to process deposit")}


def _withdraw_account(account_no: int, amount: float) -> dict:
    """Withdraw funds from an account."""
    result = call_bank_api("PATCH", f"/account/{account_no}/withdraw", {"amount": float(amount)})
    if result["success"]:
        data = result["data"]
        return {
            "success": True,
            "data": {
                "account_no": account_no,
                "name": data.get("name"),
                "amount_withdrawn": amount,
                "new_balance": data.get("new_balance", data.get("balance")),
                "currency": "GBP",
            },
        }
    return {"success": False, "error": result.get("error", "Failed to process withdrawal")}


def _get_banking_info(query_type: str) -> dict:
    """Get general banking information."""
    key = query_type.lower().replace(" ", "_").replace("-", "_")
    key = QUERY_ALIASES.get(key, key)
    if key in BANKING_INFO:
        return {"success": True, "data": BANKING_INFO[key]}
    return {"success": True, "data": {"available_topics": list(BANKING_INFO.keys())}}


# MCP Tool wrappers (thin layer for MCP protocol)
@mcp.tool()
def get_account_tool(account_no: int) -> dict:
    """Get account info (balance, name)."""
    return _get_account(account_no)


@mcp.tool()
def topup_account_tool(account_no: int, amount: float) -> dict:
    """Deposit funds into an account."""
    return _topup_account(account_no, amount)


@mcp.tool()
def withdraw_account_tool(account_no: int, amount: float) -> dict:
    """Withdraw funds from an account."""
    return _withdraw_account(account_no, amount)


@mcp.tool()
def get_banking_info_tool(query_type: str) -> dict:
    """Get banking information (rates, fees, limits, services, etc)."""
    return _get_banking_info(query_type)


def execute_tool(tool_name: str, args: dict) -> dict:
    """Execute a tool by name with given arguments."""
    logger.info(f"Executing tool: {tool_name} with args: {args}")

    if tool_name == "get_account_tool":
        result = _get_account(int(args.get("account_no")))
    elif tool_name == "topup_account_tool":
        result = _topup_account(int(args.get("account_no")), float(args.get("amount")))
    elif tool_name == "withdraw_account_tool":
        result = _withdraw_account(int(args.get("account_no")), float(args.get("amount")))
    elif tool_name == "get_banking_info_tool":
        result = _get_banking_info(str(args.get("query_type", "services")))
    else:
        logger.error(f"Unknown tool: {tool_name}")
        return {"success": False, "error": f"Unknown tool: {tool_name}"}

    logger.info(f"Tool result: {result}")
    return result


# Create HTTP app from MCP
http_app = mcp.http_app()

# Integrate with FastAPI
app.mount("/mcp", http_app)


# Chat endpoint with Google ADK integration
@app.post("/chat")
async def chat(request: ChatRequest, req: Request):
    """
    Chat endpoint with Google ADK for natural language banking.
    Google ADK calls MCP tools for account operations and banking info.
    """
    try:
        # Session management
        session_id = request.session_id or get_session_id(req)
        cleanup_old_sessions()
        last_activity[session_id] = datetime.now()

        logger.info(f"Session {session_id}: {request.message}")

        # Get conversation history
        history = conversation_sessions[session_id]
        history.append({"role": "user", "content": request.message})

        # Build context from recent history
        recent_history = history[-10:]
        if len(recent_history) > 1:
            context_parts = [
                f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
                for m in recent_history[:-1]
            ]
            context_str = chr(10).join(context_parts)
            full_message = (
                f"{SYSTEM_INSTRUCTION}\n\n"
                f"Conversation history:\n{context_str}\n\n"
                f"Current user message: {request.message}"
            )
        else:
            full_message = f"{SYSTEM_INSTRUCTION}\n\nUser message: {request.message}"

        # Call Google ADK with MCP tools
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=full_message,
            config=types.GenerateContentConfig(tools=BANKING_TOOLS, temperature=0.3),
        )

        # Process response with tool calling loop
        for _ in range(5):  # Max iterations
            # Extract function calls
            function_calls = []
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    has_fc = hasattr(part, "function_call") and part.function_call
                    has_name = has_fc and hasattr(part.function_call, "name")
                    if has_name:
                        function_calls.append(part.function_call)

            if not function_calls:
                # No tool calls - extract text response
                for part in response.candidates[0].content.parts if response.candidates else []:
                    if hasattr(part, "text") and part.text:
                        history.append({"role": "assistant", "content": part.text})
                        return {"reply": part.text}
                break

            # Execute tool calls
            function_responses = []
            tool_summary = []
            for fc in function_calls:
                args = dict(fc.args) if fc.args else {}
                logger.info(f"Tool call: {fc.name}({args})")

                result = execute_tool(fc.name, args)
                logger.info(f"Tool result: {result}")

                # Track tool calls for history
                tool_summary.append(f"[Tool: {fc.name}({args}) → {result}]")

                function_responses.append(
                    types.Part(
                        function_response=types.FunctionResponse(
                            name=fc.name, response={"result": result}
                        )
                    )
                )

            # Store tool execution in history for context
            if tool_summary:
                history.append({"role": "assistant", "content": " ".join(tool_summary)})

            # Continue conversation with tool results
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    types.Content(role="user", parts=[types.Part(text=full_message)]),
                    response.candidates[0].content,
                    types.Content(role="function", parts=function_responses),
                ],
                config=types.GenerateContentConfig(tools=BANKING_TOOLS, temperature=0.3),
            )

        # Fallback
        fallback = "I'm sorry, I couldn't process that request. Please try again."
        history.append({"role": "assistant", "content": fallback})
        return {"reply": fallback}

    except Exception as e:
        logger.error(f"Chat error: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Chat processing error: {e!s}") from e


# Health check endpoint
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "MCP Server"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)

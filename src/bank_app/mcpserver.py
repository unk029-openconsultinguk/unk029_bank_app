"""
Pure MCP Server - Banking Tools
Exposes banking tools via FastMCP for AI agents to discover and call.

Architecture:
- FastMCP exposes tools via HTTP
- Simple chat client processes user queries directly
- Tools interact with Bank API
"""

import logging
import os
from typing import Any

from fastapi import FastAPI, Request
from fastmcp import FastMCP
import httpx
from pydantic import BaseModel

# Import the Gemini banking client
from bank_app.simple_client import GeminiBankingClient

# Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Bank MCP Server")
mcp = FastMCP("Bank MCP")

# Bank API URL
BANK_API = os.getenv("BANK_API_URL", "http://unk029_bank_app:8001")

# Initialize Gemini client for chat
simple_client = GeminiBankingClient(mcp_server_url="http://localhost:8002")

# BANKING DATA
BANKING_INFO = {
    "rates": "Savings: 3.5% | Current: 0.1% | Fixed 1yr: 4.8%",
    "fees": "UK ATM: Free | International: £1.50 + 2.75% | Transfers: Free (UK)",
    "limits": "Daily ATM: £500 | Card: £10,000 | Transfer: £25,000",
    "services": "Current, Savings, Credit Cards, Mobile App, 24/7 AI Support",
    "hours": "Online: 24/7 | Phone: 8am-10pm | Branches: 9am-5pm (Mon-Fri)",
    "contact": "☎ 0800 123 4567 | 📧 support@unk029bank.com",
}

# MCP TOOLS (exposed via FastMCP)


@mcp.tool()
def check_balance(account_no: int) -> dict[str, Any]:
    """Check account balance"""
    try:
        response = httpx.get(f"{BANK_API}/account/{account_no}", timeout=5.0)
        if response.status_code == 200:
            data = response.json()
            return {
                "account": account_no,
                "name": data.get("name"),
                "balance": f"£{data.get('balance', 0):.2f}",
            }
        return {"error": f"Account {account_no} not found"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def deposit_money(account_no: int, amount: float) -> dict[str, Any]:
    """Deposit money into account"""
    try:
        response = httpx.patch(
            f"{BANK_API}/account/{account_no}/topup",
            json={"amount": amount},
            timeout=5.0,
        )
        if response.status_code == 200:
            data = response.json()
            return {
                "account": account_no,
                "deposited": f"£{amount:.2f}",
                "new_balance": f"£{data.get('new_balance', data.get('balance', 0)):.2f}",
            }
        return {"error": "Deposit failed"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def withdraw_money(account_no: int, amount: float) -> dict[str, Any]:
    """Withdraw money from account"""
    try:
        response = httpx.patch(
            f"{BANK_API}/account/{account_no}/withdraw",
            json={"amount": amount},
            timeout=5.0,
        )
        if response.status_code == 200:
            data = response.json()
            return {
                "account": account_no,
                "withdrawn": f"£{amount:.2f}",
                "new_balance": f"£{data.get('new_balance', data.get('balance', 0)):.2f}",
            }
        return {"error": "Withdrawal failed"}
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def get_bank_info(topic: str) -> dict[str, Any]:
    """Get banking information (rates/fees/limits/services/hours/contact)"""
    key = topic.lower().strip()
    # Aliases
    if key in ["rate", "interest"]:
        key = "rates"
    elif key in ["fee", "charge", "cost"]:
        key = "fees"
    elif key in ["limit", "maximum"]:
        key = "limits"
    elif key in ["service", "product"]:
        key = "services"
    elif key in ["hour", "time", "open"]:
        key = "hours"
    elif key in ["phone", "email", "call"]:
        key = "contact"

    info = BANKING_INFO.get(key)
    if info:
        return {topic: info}
    return {"available_topics": list(BANKING_INFO.keys())}


# ============================================================================
# FASTAPI ENDPOINTS
# ============================================================================


class ChatRequest(BaseModel):
    message: str


@app.post("/chat")
async def chat(request: ChatRequest, http_request: Request) -> dict[str, str]:
    """
    Chat endpoint - Process banking queries with simple client
    Maintains session context per client IP
    """
    try:
        # Get client identifier (IP address or default)
        client_id = http_request.client.host if http_request.client else "default"
        logger.info(f"User [{client_id}]: {request.message}")

        # Process with simple client (maintains session per client)
        reply = simple_client.process_query(request.message, client_id=client_id)

        return {"reply": reply}

    except Exception as e:
        logger.error(f"Error: {e}")
        return {"reply": f"Error: {e!s}"}


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check"""
    return {"status": "ok"}


# Mount MCP app at /mcp endpoint
app.mount("/mcp", mcp.http_app())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)

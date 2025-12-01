"""
MCP Server - Banking Transaction Tools
Uses FastAPI with FastMCP integration.
MCP tools are exposed via HTTP endpoints.
"""

from fastapi import FastAPI
from fastmcp import FastMCP
import httpx

# Create FastAPI app
app = FastAPI(title="UNK029 Bank MCP Server")

# Initialize FastMCP
mcp = FastMCP("UNK029 Bank MCP")

# MCP Tool 1: Get Account Information
@mcp.tool()
def get_account_tool(account_no: int) -> dict:
    """
    Get account information (balance, name, account number).
    Calls FastAPI endpoint to retrieve account details from database.
    
    Args:
        account_no: The account number
        
    Returns:
        Account details including balance, name, and account number
    """
    try:
        with httpx.Client(timeout=5.0) as client:
            # Call the FastAPI bank app endpoint (running on port 8001)
            response = client.get(f"http://unk029_bank_app:8001/account/{account_no}")
            if response.status_code == 200:
                account = response.json()
                return {
                    "success": True,
                    "data": {
                        "account_no": account.get("account_no"),
                        "name": account.get("name"),
                        "balance": account.get("balance"),
                        "currency": "GBP"
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"Account #{account_no} not found"
                }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# MCP Tool 2: Topup Account (Deposit)
@mcp.tool()
def topup_account_tool(account_no: int, amount: float) -> dict:
    """
    Deposit funds into an account.
    Calls FastAPI endpoint to process the deposit.
    
    Args:
        account_no: The account number
        amount: The amount to deposit
        
    Returns:
        Success status and new balance
    """
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.patch(
                f"http://unk029_bank_app:8001/account/{account_no}/topup",
                json={"amount": float(amount)}
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "data": {
                        "account_no": account_no,
                        "name": result.get("name"),
                        "amount_deposited": amount,
                        "new_balance": result.get("new_balance", result.get("balance")),
                        "currency": "GBP"
                    }
                }
            else:
                error_data = response.json() if response.headers.get("content-type") == "application/json" else {}
                return {
                    "success": False,
                    "error": error_data.get("detail", "Failed to process deposit")
                }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# MCP Tool 3: Withdraw from Account
@mcp.tool()
def withdraw_account_tool(account_no: int, amount: float) -> dict:
    """
    Withdraw funds from an account.
    Calls FastAPI endpoint to process the withdrawal.
    
    Args:
        account_no: The account number
        amount: The amount to withdraw
        
    Returns:
        Success status and new balance
    """
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.patch(
                f"http://unk029_bank_app:8001/account/{account_no}/withdraw",
                json={"amount": float(amount)}
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "data": {
                        "account_no": account_no,
                        "name": result.get("name"),
                        "amount_withdrawn": amount,
                        "new_balance": result.get("new_balance", result.get("balance")),
                        "currency": "GBP"
                    }
                }
            else:
                error_data = response.json() if response.headers.get("content-type") == "application/json" else {}
                return {
                    "success": False,
                    "error": error_data.get("detail", "Failed to process withdrawal")
                }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# Create HTTP app from MCP
http_app = mcp.http_app()

# Integrate with FastAPI
app.mount("/mcp", http_app)

# Health check endpoint
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "MCP Server"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

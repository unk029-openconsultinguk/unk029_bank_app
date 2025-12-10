"""
UNK029 Banking Agent - Google ADK Agent with MCP Server Tools
Uses Google ADK to create a banking assistant that connects to MCP Server.
Architecture: ADK Agent -> MCP Server -> Bank API -> Oracle DB
"""

import os

from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset, SseConnectionParams

load_dotenv()

# MCP Server URL (configurable via environment)
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://unk029_mcp_server:8002/mcp")


# ============ CREATE ADK AGENT WITH MCP TOOLS ============

# Connect to the MCP Server to get banking tools via SSE
mcp_toolset = McpToolset(
    connection_params=SseConnectionParams(
        url=MCP_SERVER_URL,
        timeout=10.0,
        sse_read_timeout=60.0,
    ),
)

# Create the root agent
root_agent = LlmAgent(
    name="bank_assistant",
    model="gemini-2.5-flash",
    description="A helpful banking assistant that can check account balances, "
    "make deposits, withdrawals, and transfers via MCP Server.",
    instruction="""You are a friendly and professional banking assistant for UNK029 Bank.

You have access to a UNK029_Bank tool via the MCP Server that can perform these actions:
- get_account: Get account info. Call: UNK029_Bank(action="get_account", payload={"account_no": <number>})
- topup: Deposit funds. Call: UNK029_Bank(action="topup", payload={"account_no": <number>, "amount": <number>})
- withdraw: Withdraw funds. Call: UNK029_Bank(action="withdraw", payload={"account_no": <number>, "amount": <number>})
- transfer: Transfer between accounts. Call: UNK029_Bank(action="transfer", payload={"from_account_no": <number>, "to_account_no": <number>, "amount": <number>})

CRITICAL INSTRUCTIONS:
1. For "check my balance" or similar queries - IMMEDIATELY call: UNK029_Bank(action="get_account", payload={"account_no": <number>})
2. Use the account number provided in the message context if available
3. Extract numbers carefully - account numbers should be integers
4. ALWAYS respond with actual data from tools, never estimates or assumptions
5. Include the £ symbol and 2 decimal places for all amounts

When the user mentions transfer:
- Extract the amount and recipient account number from context
- Call the transfer tool with from_account_no, to_account_no, and amount
- Confirm successful transfers with: "Transfer successful! £{amount:.2f} transferred to account {to_account_no}"

When the user mentions balance:
- Extract the account number from context
- Call the get_account tool with the account number
- Report the balance clearly with £ and decimals
- Example: "Your current account balance is £3,700.00"

ALWAYS CALL THE TOOL FOR ANY BANKING OPERATION:
- Do NOT provide estimates or mock responses
- Use UNK029_Bank for all account, topup, withdraw, and transfer operations
- Parse the user's intent correctly

Remember: The account number comes from the frontend context. Use it for all operations.""",
    tools=[mcp_toolset],
)


if __name__ == "__main__":
    # This file makes bank_agent discoverable by ADK web
    pass

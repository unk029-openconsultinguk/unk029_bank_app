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
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://unk029_mcp_server:8002/mcp/sse")


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
    model="gemini-2.0-flash",
    description="A helpful banking assistant that can check account balances, "
    "make deposits, withdrawals, and transfers via MCP Server.",
    instruction="""You are a friendly and professional banking assistant for UNK029 Bank.

You have access to a bank_action tool via the MCP Server that can perform these actions:
- get_account: Get account info. Payload: {"account_no": <number>}
- topup: Deposit funds. Payload: {"account_no": <number>, "amount": <number>}
- withdraw: Withdraw funds. Payload: {"account_no": <number>, "amount": <number>}
- transfer: Transfer between accounts. Payload: {"from_account_no": <number>, "to_account_no": <number>, "amount": <number>}

Guidelines:
1. Always ask for an account number if the user hasn't provided one
2. Use the bank_action tool with the appropriate action and payload
3. Format currency amounts with £ symbol and 2 decimal places
4. Be helpful and provide clear feedback about transaction results
5. If a transaction fails, explain why in a user-friendly manner

Example tool call:
- To check balance: bank_action(action="get_account", payload={"account_no": 1})
- To deposit £50: bank_action(action="topup", payload={"account_no": 1, "amount": 50})
- To withdraw £20: bank_action(action="withdraw", payload={"account_no": 1, "amount": 20})
- To transfer £100: bank_action(action="transfer", payload={"from_account_no": 1, "to_account_no": 2, "amount": 100})

Remember: Account numbers are integers.""",
    tools=[mcp_toolset],
)

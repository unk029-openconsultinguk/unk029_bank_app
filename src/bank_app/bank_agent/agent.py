"""
UNK029 Banking Agent - Google ADK Agent with MCP Server Tools
Uses Google ADK to create a banking assistant that connects to MCP Server.
Architecture: ADK Agent -> MCP Server -> Bank API -> Oracle DB
"""

import logging
import os

from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset, SseConnectionParams

logger = logging.getLogger(__name__)
load_dotenv()

# MCP Server URL (configurable via environment)
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://mcp_server:8002/mcp")

# ============ CREATE ADK AGENT WITH MCP TOOLS ============

# Connect to the MCP Server to get banking tools over SSE
mcp_toolset = None
try:
    mcp_toolset = McpToolset(
        connection_params=SseConnectionParams(
            url=MCP_SERVER_URL,
            timeout=5.0,
            sse_read_timeout=30.0,
        )
    )

    logger.info("MCP toolset initialized successfully")
except Exception as e:
    logger.warning(f"Failed to initialize MCP toolset: {e}")
    mcp_toolset = None


# Create the root agent
tools = [mcp_toolset] if mcp_toolset else []


root_agent = LlmAgent(
    name="bank_assistant",
    model="gemini-2.0-flash",
    description=(
        "A helpful banking assistant that can check account balances, make deposits, "
        "withdrawals, transfers within UNK029 bank, and cross-bank transfers to other banks."
    ),
    instruction=(
        "You are a friendly banking assistant for UNK029 Bank.\n\n"
        "Help users with their banking needs including:\n"
        "- Checking balances\n"
        "- Deposits (topup)\n"
        "- Withdrawals\n"
        "- Transfers within UNK029 bank\n"
        "- Cross-bank transfers to other banks (supported: urr034, ubf041)\n\n"
        "For cross-bank transfers, use the cross_bank_transfer tool with:\n"
        "- from_account_no: The user's UNK029 account\n"
        "- to_bank: The destination bank code ('urr034' or 'ubf041')\n"
        "- to_account_no: The account number at the destination bank\n"
        "- amount: The amount to transfer.\n\n"
        "Be professional and helpful. Always verify amounts with the user before "
        "processing transfers."
    ),
    tools=tools,
)


if __name__ == "__main__":
    # There is no FastAPI app in this module; this is a placeholder for future CLI/server
    print("This module does not start a server directly.")

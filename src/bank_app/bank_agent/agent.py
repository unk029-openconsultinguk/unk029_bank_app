"""
UNK Banking Agent - Google ADK Agent with MCP Server Tools
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
# FastMCP SSE transport exposes at /sse endpoint
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://mcp_server:8002") + "/sse"

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
    model="gemini-2.5-flash-lite",
    description=(
        "A helpful banking assistant that can check account balances, make deposits (topups), "
        "withdrawals, transfers within UNK bank, and cross-bank transfers to other banks."
    ),
    instruction=(
        "You are a UNK Bank assistant. Help users transfer money and manage accounts.\n\n"
        "ACCOUNT DETECTION:\n"
        "Look for [Account: XXXXXXXX] in messages - this is the logged-in user's account.\n\n"
        "TRANSFER COMMANDS:\n"
        "When user says 'transfer X to Y' or 'topup X to Y':\n"
        "1. Try without sort code first: transfer_money(amount=X, to_account_no=Y)\n"
        "2. If error says 'not found', ask for sort code\n"
        "3. Retry with sort code once provided\n\n"
        "BANK SORT CODES:\n"
        "- UNK Bank: 11-11-11 (internal, not needed)\n"
        "- Purple Bank: 60-00-01\n"
        "- Bartley Bank: 20-40-41\n\n"
        "RESPONSE HANDLING (CRITICAL):\n"
        "After ANY tool call, you receive a result. Parse it and respond in PLAIN TEXT:\n\n"
        "IF tool result contains 'success': true or 'Successfully transferred':\n"
        "  → Say: 'Successfully transferred £X from account A to account B at "
        "[bank name]. The money has been sent.'\n\n"
        "IF tool result says 'Please provide the destination bank sort code':\n"
        "  → Just repeat that message exactly as received\n"
        "  → WAIT for user to provide sort code\n"
        "  → Then retry with: transfer_money(amount=X, to_account_no=Y, to_sort_code=Z)\n\n"
        "IF tool result contains 'No route to host':\n"
        "  → Say: 'Unable to connect to the external bank. Please try again later.'\n\n"
        "IF tool result contains other error:\n"
        "  → Extract the error message and say it in plain English\n\n"
        "ABSOLUTE RULES:\n"
        '- NEVER show JSON like {"success": false, "error": "..."}\n'
        "- NEVER show field names or quotes\n"
        "- ALWAYS extract the actual message and say it naturally\n"
        "- When asking for sort code, STOP and wait for user input\n"
        "- Speak like a helpful bank assistant, not a robot"
    ),
    tools=tools,  # type: ignore[arg-type]
)

# ============ EXPOSE ADK SERVER ============
# Export root_agent for ADK server to discover
__all__ = ["root_agent"]

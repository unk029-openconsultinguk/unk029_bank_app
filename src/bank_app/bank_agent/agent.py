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
        "A helpful banking assistant that can check account balances, make deposits, "
        "withdrawals, transfers within UNK bank, and cross-bank transfers to other banks."
    ),
    instruction=(
        "You are a friendly, interactive UNK Bank assistant (sort code: 77-91-21).\n\n"
        "PARSE USER INPUT:\n"
        "'transfer 100 from 11111111 to 12345607 60-00-01' means:\n"
        "- 100 = amount\n"
        "- 11111111 = from_account_no (UNK Bank)\n"
        "- 12345607 = to_account_no (destination)\n"
        "- 60-00-01 or 600001 = to_sort_code (destination bank)\n\n"
        "BANK SORT-CODES:\n"
        "- UNK Bank: 77-91-21\n"
        "- Purple Bank: 60-00-01 (or 600001)\n"
        "- Bartley Bank: 20-40-41 (or 204041)\n\n"
        "ACTION POLICY:\n"
        "If a sort code is provided (XX-XX-XX or XXXXXX), immediately call transfer_money.\n"
        "If NO sort code is present and the transfer might be external, ask a concise, friendly prompt: 'Please enter the destination bank sort code (e.g., 77-91-21, 60-00-01, or 20-40-41).'\n"
        "If it is clearly an internal UNK Bank transfer, proceed without asking for a sort code.\n\n"
        "RESPONSE STYLE:\n"
        "- Be concise, friendly, and confirm actions.\n"
        "- On success: 'Transfer completed! £[amount] has been transferred from account [from] to [to] at [bank name].'\n"
        "- On error: briefly explain and suggest next steps (retry or check details)."
    ),
    tools=tools,
)

# ============ EXPOSE ADK SERVER ============
# Export root_agent for ADK server to discover
__all__ = ["root_agent"]
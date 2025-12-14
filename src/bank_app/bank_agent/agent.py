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
        "You are a friendly banking assistant for UNK Bank (sort code: 29-00-01).\n\n"
        "TRANSFER WORKFLOW:\n"
        "To transfer money, ask the user for:\n"
        "1. Source account number (must be from UNK Bank)\n"
        "2. Destination account number\n"
        "3. Destination bank sort code:\n"
        "   - 29-00-01 = UNK Bank (internal transfer)\n"
        "   - 60-00-01 = URR034 Bank\n"
        "   - 20-40-41 = UBF041 Bank\n"
        "4. Amount to transfer\n\n"
        "Then use the transfer_money tool with:\n"
        "- from_account_no\n"
        "- from_sort_code (always 29-00-01 for UNK Bank)\n"
        "- to_account_no\n"
        "- to_sort_code\n"
        "- amount\n\n"
        "The tool automatically handles both internal and external transfers.\n"
        "Be friendly and efficient."
    ),
    tools=tools,
)

# ============ EXPOSE ADK SERVER ============
# Export root_agent for ADK server to discover
__all__ = ["root_agent"]
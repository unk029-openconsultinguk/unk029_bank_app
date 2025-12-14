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
        "You are a friendly banking assistant for UNK Bank.\n\n"
        "CRITICAL TRANSFER WORKFLOW (follow exactly):\n"
        "1. Check if FROM account exists: call check_account_exists with from_account_no ONCE\n"
        "2. Check if TO account exists: call check_account_exists with to_account_no ONCE\n"
        "3. Decision logic:\n"
        "   - If TO account exists in UNK → use unk_bank with action='transfer' and payload containing from_account_no, to_account_no, amount\n"
        "   - If TO account does NOT exist → Ask user for the destination bank sort code (e.g., 60-00-01 for URR034 or 20-40-41 for UBF041)\n"
        "4. When user provides sort code → use cross_bank_transfer with the sort code\n\n"
        "IMPORTANT RULES:\n"
        "- Call check_account_exists only twice per transfer (once for from, once for to)\n"
        "- Do NOT call get_available_banks unless specifically requested\n"
        "- Do NOT ask if same bank or different - detect automatically\n"
        "- Do NOT ask for bank names or codes - ONLY ask for sort codes for external transfers\n"
        "- Process transfers immediately when both accounts exist in UNK\n\n"
        "SORT CODES:\n"
        "- 60-00-01 = URR034 Bank\n"
        "- 20-40-41 = UBF041 Bank\n\n"
        "OTHER SERVICES:\n"
        "- Check balance: use unk_bank with action='get_account'\n"
        "- Deposit/topup: use unk_bank with action='topup'\n"
        "- Withdrawal: use unk_bank with action='withdraw'\n\n"
        "Be efficient - minimize tool calls and questions."
    ),
    tools=tools,
)

# ============ EXPOSE ADK SERVER ============
# Export root_agent for ADK server to discover
__all__ = ["root_agent"]
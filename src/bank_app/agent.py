"""
Root Banking Agent - Uses Google ADK (google-genai) with MCP Server Tools
Agent calls MCP Server tools to process banking queries.
Architecture: Agent -> MCP Server -> Bank API -> Oracle DB
"""

from datetime import datetime, timedelta
import os
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from google import genai
from google.genai import types
import httpx
from pydantic import BaseModel

load_dotenv()

# Configure Google ADK client
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable not set")

client = genai.Client(api_key=GOOGLE_API_KEY)

app = FastAPI(title="UNK029 Root Banking Agent")


# Request/Response models
class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


# Session state and cache
session_state: dict[str, list[dict[str, str]]] = {}
response_cache: dict[str, tuple[str, datetime]] = {}
CACHE_TTL = 300  # 5 minutes


def get_cached_response(message: str) -> str | None:
    """Get cached response if available and not expired."""
    cache_key = message.lower().strip()
    if cache_key in response_cache:
        cached, timestamp = response_cache[cache_key]
        if datetime.now() - timestamp < timedelta(seconds=CACHE_TTL):
            print(f"DEBUG: Cache hit for: {message[:50]}", flush=True)
            return cached
        else:
            del response_cache[cache_key]
    return None


def cache_response(message: str, response: str) -> None:
    """Cache response with current timestamp."""
    cache_key = message.lower().strip()
    response_cache[cache_key] = (response, datetime.now())
    if len(response_cache) > 100:
        oldest_key = min(response_cache.keys(), key=lambda k: response_cache[k][1])
        del response_cache[oldest_key]


def _get_session_key(request: Request | None) -> str:
    """Get session key from client IP."""
    return request.client.host if request and request.client else "default"


def call_mcp_tool(tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
    """
    Call MCP Server tools via REST endpoints.
    Agent communicates with MCP Server to execute banking operations.
    """
    try:
        if not tool_input:
            return {"error": "Invalid tool input"}

        with httpx.Client(timeout=10.0) as http_client:
            mcp_url = "http://unk029_mcp_server:8002"

            print(f"DEBUG: Calling MCP tool {tool_name} with input: {tool_input}", flush=True)

            if tool_name == "get_account_info":
                account_no = int(tool_input.get("account_no", 0))
                response = http_client.get(f"{mcp_url}/account/{account_no}")
                if response.status_code == 200:
                    data = response.json()
                    return {"success": True, "data": data}
                else:
                    return {"error": f"Account {account_no} not found"}

            elif tool_name == "deposit_funds":
                account_no = int(tool_input.get("account_no", 0))
                amount = float(tool_input.get("amount", 0))
                response = http_client.patch(
                    f"{mcp_url}/account/{account_no}/topup", json={"amount": amount}
                )
                if response.status_code == 200:
                    data = response.json()
                    return {"success": True, "data": data}
                else:
                    return {"error": "Deposit failed"}

            elif tool_name == "withdraw_funds":
                account_no = int(tool_input.get("account_no", 0))
                amount = float(tool_input.get("amount", 0))
                response = http_client.patch(
                    f"{mcp_url}/account/{account_no}/withdraw", json={"amount": amount}
                )
                if response.status_code == 200:
                    data = response.json()
                    return {"success": True, "data": data}
                else:
                    return {"error": "Withdrawal failed"}
            else:
                return {"error": f"Unknown tool: {tool_name}"}

    except Exception as e:
        print(f"Tool execution error: {e}", flush=True)
        return {"error": f"Failed to call tool: {e!s}"}


# Define tools for Google ADK
AGENT_TOOLS = [
    types.Tool(
        function_declarations=[
            types.FunctionDeclaration(
                name="get_account_info",
                description="Get account info: balance, name, account number",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "account_no": types.Schema(
                            type=types.Type.INTEGER,
                            description="The account number to query",
                        ),
                    },
                    required=["account_no"],
                ),
            ),
            types.FunctionDeclaration(
                name="deposit_funds",
                description="Deposit funds into a bank account",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "account_no": types.Schema(
                            type=types.Type.INTEGER,
                            description="The account number to deposit to",
                        ),
                        "amount": types.Schema(
                            type=types.Type.NUMBER,
                            description="The amount to deposit in GBP",
                        ),
                    },
                    required=["account_no", "amount"],
                ),
            ),
            types.FunctionDeclaration(
                name="withdraw_funds",
                description="Withdraw funds from a bank account",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "account_no": types.Schema(
                            type=types.Type.INTEGER,
                            description="The account number to withdraw from",
                        ),
                        "amount": types.Schema(
                            type=types.Type.NUMBER,
                            description="The amount to withdraw in GBP",
                        ),
                    },
                    required=["account_no", "amount"],
                ),
            ),
        ]
    )
]

SYSTEM_PROMPT = """You are a friendly banking assistant. \
You have access to the following tools:
- get_account_info: Get account balance and information
- deposit_funds: Deposit money into an account
- withdraw_funds: Withdraw money from an account

When the user asks about their account, use the appropriate tool to get the information.
Always extract account number and amount from user messages.
Respond in a friendly and helpful manner."""


async def process_chat(message: str, request: Request | None = None) -> str:
    """
    Process user message with Google ADK (Gemini) using MCP Server tools.
    """
    # Check cache first
    cached = get_cached_response(message)
    if cached:
        return cached

    print(f"DEBUG: Processing message: {message}", flush=True)

    try:
        # Build full prompt with system instruction
        full_message = f"{SYSTEM_PROMPT}\n\nUser: {message}"

        # Call Gemini with tools
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[types.Content(role="user", parts=[types.Part(text=full_message)])],
            config=types.GenerateContentConfig(tools=list(AGENT_TOOLS), temperature=0.3),
        )

        print(f"DEBUG: Gemini response candidates: {response.candidates}", flush=True)

        # Process tool calls if Gemini decides to use tools
        max_iterations = 5
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            if not response.candidates or not response.candidates[0].content:
                break

            content = response.candidates[0].content
            if not content.parts:
                break

            # Check for function calls
            function_call = None
            for part in content.parts:
                if part.function_call:
                    function_call = part.function_call
                    break

            if not function_call:
                # No function call, we have the final response
                break

            # Execute the tool
            tool_name = function_call.name or ""
            if not tool_name:
                break
            tool_args: dict[str, Any] = dict(function_call.args) if function_call.args else {}

            # Convert float to int for account_no
            if "account_no" in tool_args and isinstance(tool_args["account_no"], float):
                tool_args["account_no"] = int(tool_args["account_no"])

            print(f"DEBUG: Gemini called tool: {tool_name} with args: {tool_args}", flush=True)

            # Call the MCP tool
            tool_result = call_mcp_tool(tool_name, tool_args)
            print(f"DEBUG: Tool result: {tool_result}", flush=True)

            # Send tool result back to Gemini
            function_response = types.Part(
                function_response=types.FunctionResponse(
                    name=tool_name,
                    response=tool_result,
                )
            )

            # Continue conversation with tool result
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    types.Content(role="user", parts=[types.Part(text=full_message)]),
                    content,
                    types.Content(role="function", parts=[function_response]),
                ],
                config=types.GenerateContentConfig(tools=list(AGENT_TOOLS), temperature=0.3),
            )

        # Extract final text response
        final_response = ""
        if response.candidates and response.candidates[0].content:
            parts = response.candidates[0].content.parts
            if parts:
                for part in parts:
                    if part.text:
                        final_response += part.text

        # Fallback response if no text generated
        if not final_response:
            final_response = (
                "I'm here to help with your banking needs. "
                "Please ask about your account balance, or deposit/withdraw funds."
            )

        cache_response(message, final_response)
        return final_response

    except Exception as e:
        print(f"Gemini error: {e}", flush=True)
        fallback = (
            "Hello! I'm your banking assistant. "
            "Ask me about your account balance, deposits, or withdrawals."
        )
        cache_response(message, fallback)
        return fallback


# Chat Endpoint
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat: ChatRequest, request: Request) -> ChatResponse:
    """Main chat endpoint - process user message via Gemini AI with MCP tools."""
    print("=== AI AGENT CHAT ENDPOINT ===", flush=True)
    print(f"Message: {chat.message}", flush=True)
    reply = await process_chat(chat.message, request)
    print(f"Reply: {reply[:100]}...", flush=True)
    return ChatResponse(reply=reply)


# Health check
@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "service": "AI Agent"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003)

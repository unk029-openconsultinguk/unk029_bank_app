"""
Root Banking Agent - Uses Google ADK (google-genai) with MCP Server Tools
Agent calls MCP Server tools to process banking queries.
Architecture: Agent -> MCP Server -> Bank API -> Oracle DB
"""

from datetime import datetime
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


# Session state
session_state: dict[str, list[dict[str, str]]] = {}


def _get_session_key(request: Request | None) -> str:
    """Get session key from client IP."""
    return request.client.host if request and request.client else "default"


def call_mcp_tool(tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
    """
    Call bank API directly to execute banking operations.
    """
    try:
        if not tool_input:
            return {"error": "Invalid tool input"}

        with httpx.Client(timeout=10.0) as http_client:
            bank_api_url = "http://unk029_bank_app:8001"

            print(f"DEBUG: Calling tool {tool_name} with input: {tool_input}", flush=True)

            # Call bank API directly
            if tool_name == "get_account_info":
                account_no = int(tool_input.get("account_no", 0))
                print(f"DEBUG: Fetching account {account_no}", flush=True)
                response = http_client.get(
                    f"{bank_api_url}/account/{account_no}"
                )
                print(f"DEBUG: Response status: {response.status_code}", flush=True)
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "account_no": data.get("account_no"),
                        "name": data.get("name"),
                        "balance": data.get("balance")
                    }
                else:
                    return {"success": False, "error": f"Account {account_no} not found"}

            elif tool_name == "deposit_funds":
                account_no = int(tool_input.get("account_no", 0))
                amount = float(tool_input.get("amount", 0))
                print(f"DEBUG: Depositing £{amount} to account {account_no}", flush=True)
                response = http_client.patch(
                    f"{bank_api_url}/account/{account_no}/topup",
                    json={"amount": amount}
                )
                print(f"DEBUG: Response status: {response.status_code}", flush=True)
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "account_no": data.get("account_no"),
                        "name": data.get("name"),
                        "new_balance": data.get("new_balance")
                    }
                else:
                    return {"success": False, "error": "Deposit failed"}

            elif tool_name == "withdraw_funds":
                account_no = int(tool_input.get("account_no", 0))
                amount = float(tool_input.get("amount", 0))
                print(f"DEBUG: Withdrawing £{amount} from account {account_no}", flush=True)
                response = http_client.patch(
                    f"{bank_api_url}/account/{account_no}/withdraw",
                    json={"amount": amount}
                )
                print(f"DEBUG: Response status: {response.status_code}", flush=True)
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "account_no": data.get("account_no"),
                        "name": data.get("name"),
                        "new_balance": data.get("new_balance")
                    }
                else:
                    error_msg = response.text
                    return {"success": False, "error": error_msg if error_msg else "Withdrawal failed"}
            else:
                return {"success": False, "error": f"Unknown tool: {tool_name}"}

    except Exception as e:
        print(f"Tool execution error: {e}", flush=True)
        return {"success": False, "error": f"Failed to call tool: {e!s}"}


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

SYSTEM_PROMPT = """You are a helpful banking assistant with access to banking tools.

IMPORTANT RULES:
1. When a user asks about "my account" or "my balance", ALWAYS ask for their account number
2. If the user provides JUST A NUMBER (like "1", "2", "123", etc.) after being asked for an account number, treat that number as the account number and call get_account_info with it
3. Account numbers are integers - if user says "1", use account_no=1
4. NEVER ask for the account number again if the user already provided a number

Available tools:
- get_account_info(account_no): Get account balance and details
- deposit_funds(account_no, amount): Deposit money
- withdraw_funds(account_no, amount): Withdraw money

Be friendly and helpful."""


async def process_chat(message: str, request: Request | None = None) -> str:
    """
    Process user message with Google ADK (Gemini) using MCP Server tools.
    """
    # Get session key
    session_key = _get_session_key(request)
    
    # Initialize session history if needed
    if session_key not in session_state:
        session_state[session_key] = []
    
    print(f"DEBUG: Processing message: {message}", flush=True)
    print(f"DEBUG: Session history length: {len(session_state[session_key])}", flush=True)

    try:
        # Build conversation history with system instruction
        conversation_contents = []
        
        # ALWAYS add system instruction at the start
        conversation_contents.append(
            types.Content(role="user", parts=[types.Part(text=SYSTEM_PROMPT)])
        )
        conversation_contents.append(
            types.Content(role="model", parts=[types.Part(text="Understood. I will follow these rules exactly.")])
        )
        
        # Add previous conversation history
        for i, hist_msg in enumerate(session_state[session_key]):
            print(f"DEBUG: History {i}: {hist_msg['role']}: {hist_msg['content'][:50]}...", flush=True)
            if hist_msg["role"] == "user":
                conversation_contents.append(
                    types.Content(role="user", parts=[types.Part(text=hist_msg["content"])])
                )
            else:
                conversation_contents.append(
                    types.Content(role="model", parts=[types.Part(text=hist_msg["content"])])
                )
        
        # Add current user message
        conversation_contents.append(
            types.Content(role="user", parts=[types.Part(text=message)])
        )

        # Call Gemini with tools
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=conversation_contents,
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
                contents=conversation_contents + [
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

        # Save conversation to session history
        session_state[session_key].append({"role": "user", "content": message})
        session_state[session_key].append({"role": "assistant", "content": final_response})
        
        # Keep only last 10 exchanges to avoid context overflow
        if len(session_state[session_key]) > 20:
            session_state[session_key] = session_state[session_key][-20:]

        return final_response

    except Exception as e:
        print(f"Gemini error: {e}", flush=True)
        fallback = (
            "Hello! I'm your banking assistant. "
            "Ask me about your account balance, deposits, or withdrawals."
        )
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


# Clear session endpoint
@app.post("/clear-session")
async def clear_session_endpoint(request: Request) -> dict[str, str]:
    """Clear conversation history for the current session."""
    session_key = _get_session_key(request)
    if session_key in session_state:
        del session_state[session_key]
        print(f"DEBUG: Cleared session for {session_key}", flush=True)
    return {"status": "ok", "message": "Session cleared"}


# Health check
@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "service": "AI Agent"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8003)

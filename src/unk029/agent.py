"""
Root Banking Agent - Uses Gemini AI with MCP Server Tools
Agent calls MCP Server tools to process banking queries.
Architecture: Agent -> MCP Server -> Bank API -> Oracle DB
"""

from fastapi import FastAPI, Request
from pydantic import BaseModel
import google.generativeai as genai
import os
from dotenv import load_dotenv
import httpx
import json
from datetime import datetime, timedelta

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

app = FastAPI(title="UNK029 Root Banking Agent")

# Request/Response models
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str


# Session state and cache
session_state = {}
response_cache = {}
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

def _get_session_key(request: Request) -> str:
    """Get session key from client IP."""
    return request.client.host if request and request.client else "default"


def call_mcp_tool(tool_name: str, tool_input: dict) -> dict:
    """
    Call MCP Server tools via HTTP.
    Agent communicates with MCP Server to execute banking operations.
    
    Args:
        tool_name: Name of the tool (get_account_info, deposit_funds, withdraw_funds)
        tool_input: Tool parameters
        
    Returns:
        Tool result as dict
    """
    try:
        with httpx.Client(timeout=10.0) as client:
            mcp_url = "http://unk029_mcp_server:8002/mcp"
            
            print(f"DEBUG: Calling MCP tool {tool_name} with input: {tool_input}", flush=True)
            
            # Map tool names to MCP tool names
            mcp_tool_map = {
                "get_account_info": "get_account_tool",
                "deposit_funds": "topup_account_tool",
                "withdraw_funds": "withdraw_account_tool"
            }
            
            mcp_tool_name = mcp_tool_map.get(tool_name)
            if not mcp_tool_name:
                return {"error": f"Unknown tool: {tool_name}"}
            
            # Prepare JSON-RPC request for the MCP tool
            request_payload = {
                "jsonrpc": "2.0",
                "id": "1",
                "method": "tools/call",
                "params": {
                    "name": mcp_tool_name,
                    "arguments": tool_input
                }
            }
            
            # Send request to MCP Server
            response = client.post(mcp_url, json=request_payload)
            
            print(f"DEBUG: MCP response status: {response.status_code}", flush=True)
            print(f"DEBUG: MCP response: {response.text}", flush=True)
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract tool result from JSON-RPC response
                if "result" in result:
                    tool_result = result.get("result", {})
                    return tool_result
                elif "error" in result:
                    error = result.get("error", {})
                    return {"error": error.get("message", "RPC error")}
                else:
                    return result
            else:
                return {"error": f"MCP Server error: {response.text}"}
                
    except Exception as e:
        print(f"Tool execution error: {e}", flush=True)
        return {"error": f"Failed to call tool: {str(e)}"}


async def process_chat(message: str, request: Request = None) -> str:
    """
    Process user message with Gemini AI using MCP Server tools.
    
    Args:
        message: User message
        request: FastAPI request object
        
    Returns:
        AI response
    """
    message_lower = message.lower().strip()
    
    # Check cache first
    cached = get_cached_response(message)
    if cached:
        return cached
    
    print(f"DEBUG: Processing message: {message}", flush=True)
    
    # Define system prompt for the agent
    system_prompt = """You are a friendly banking assistant. You have access to the following tools:
- get_account_info: Get account balance and information
- deposit_funds: Deposit money into an account
- withdraw_funds: Withdraw money from an account

When the user asks about their account, use the appropriate tool to get the information.
Always extract account number and amount from user messages.
Respond in a friendly and helpful manner."""
    
    try:
        # Create Gemini model with tools
        model = genai.GenerativeModel(
            "gemini-2.5-flash",
            tools=[
                genai.protos.Tool(
                    function_declarations=[
                        genai.protos.FunctionDeclaration(
                            name="get_account_info",
                            description="Get account information including balance, name, and account number",
                            parameters=genai.protos.Schema(
                                type_="OBJECT",
                                properties={
                                    "account_no": genai.protos.Schema(
                                        type_="INTEGER",
                                        description="The account number to query"
                                    )
                                },
                                required=["account_no"]
                            )
                        ),
                        genai.protos.FunctionDeclaration(
                            name="deposit_funds",
                            description="Deposit funds into a bank account",
                            parameters=genai.protos.Schema(
                                type_="OBJECT",
                                properties={
                                    "account_no": genai.protos.Schema(
                                        type_="INTEGER",
                                        description="The account number to deposit to"
                                    ),
                                    "amount": genai.protos.Schema(
                                        type_="NUMBER",
                                        description="The amount to deposit in GBP"
                                    )
                                },
                                required=["account_no", "amount"]
                            )
                        ),
                        genai.protos.FunctionDeclaration(
                            name="withdraw_funds",
                            description="Withdraw funds from a bank account",
                            parameters=genai.protos.Schema(
                                type_="OBJECT",
                                properties={
                                    "account_no": genai.protos.Schema(
                                        type_="INTEGER",
                                        description="The account number to withdraw from"
                                    ),
                                    "amount": genai.protos.Schema(
                                        type_="NUMBER",
                                        description="The amount to withdraw in GBP"
                                    )
                                },
                                required=["account_no", "amount"]
                            )
                        ),
                    ]
                )
            ],
            system_instruction=system_prompt
        )
        
        # Initial chat with Gemini
        print(f"DEBUG: Calling Gemini with message: {message}", flush=True)
        chat = model.start_chat()
        response = chat.send_message(message)
        
        print(f"DEBUG: Gemini response: {response}", flush=True)
        
        # Process tool calls if Gemini decides to use tools
        max_iterations = 5
        iteration = 0
        
        while response.candidates[0].content.parts and iteration < max_iterations:
            iteration += 1
            last_part = response.candidates[0].content.parts[-1]
            
            # Check if Gemini wants to call a tool
            if hasattr(last_part, 'function_call'):
                tool_call = last_part.function_call
                tool_name = tool_call.name
                tool_args = {key: value for key, value in tool_call.args.items()}
                
                print(f"DEBUG: Gemini called tool: {tool_name} with args: {tool_args}", flush=True)
                
                # Call the MCP tool
                tool_result = call_mcp_tool(tool_name, tool_args)
                
                print(f"DEBUG: Tool result: {tool_result}", flush=True)
                
                # Send tool result back to Gemini
                response = chat.send_message(
                    genai.protos.Content(
                        parts=[
                            genai.protos.Part.from_function_response(
                                name=tool_name,
                                response=tool_result
                            )
                        ]
                    )
                )
            else:
                # No more tool calls, break the loop
                break
        
        # Extract final text response from Gemini
        final_response = ""
        if response.candidates:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'text') and part.text:
                    final_response += part.text
        
        # Fallback response if no text generated
        if not final_response:
            final_response = "I'm here to help with your banking needs. Please ask about your account balance, or if you'd like to deposit or withdraw funds."
        
        cache_response(message, final_response)
        return final_response
        
    except Exception as e:
        print(f"Gemini error: {e}", flush=True)
        fallback = "Hello! I'm your banking assistant. Ask me about your account balance, deposits, or withdrawals."
        cache_response(message, fallback)
        return fallback


# Chat Endpoint
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat: ChatRequest, request: Request):
    """Main chat endpoint - process user message via Gemini AI with MCP tools."""
    print(f"=== AI AGENT CHAT ENDPOINT ===", flush=True)
    print(f"Message: {chat.message}", flush=True)
    reply = await process_chat(chat.message, request)
    print(f"Reply: {reply[:100]}...", flush=True)
    return ChatResponse(reply=reply)


# Health check
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "service": "AI Agent"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)

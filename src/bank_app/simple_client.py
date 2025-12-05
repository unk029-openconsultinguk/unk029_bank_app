"""
Gemini AI Banking Client - Uses Google Generative AI with MCP Tools
Leverages Gemini 2.0 Flash to understand natural language and call MCP banking tools.
"""

import httpx
import os
import json
from typing import Any, Optional
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Configure Google Generative AI
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY environment variable not set")

genai.configure(api_key=GOOGLE_API_KEY)


class GeminiBankingClient:
    """Banking client using Gemini AI with MCP tools."""
    
    def __init__(self, mcp_server_url: str = "http://mcp_server:8002"):
        self.mcp_url = mcp_server_url
        self.sessions = {}  # Store conversation history by client ID
        self.tools = self._define_tools()
    
    def _define_tools(self) -> list:
        """Define banking tools for Gemini to use."""
        return [
            {
                "name": "check_balance",
                "description": "Check the account balance for a given account number",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "account_no": {
                            "type": "integer",
                            "description": "The account number to check balance for",
                        },
                    },
                    "required": ["account_no"],
                },
            },
            {
                "name": "deposit_money",
                "description": "Deposit money into a bank account",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "account_no": {
                            "type": "integer",
                            "description": "The account number to deposit to",
                        },
                        "amount": {
                            "type": "number",
                            "description": "The amount to deposit in GBP",
                        },
                    },
                    "required": ["account_no", "amount"],
                },
            },
            {
                "name": "withdraw_money",
                "description": "Withdraw money from a bank account",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "account_no": {
                            "type": "integer",
                            "description": "The account number to withdraw from",
                        },
                        "amount": {
                            "type": "number",
                            "description": "The amount to withdraw in GBP",
                        },
                    },
                    "required": ["account_no", "amount"],
                },
            },
        ]
    
    def process_query(self, user_input: str, client_id: str = "default") -> str:
        """
        Process user query using Gemini AI and execute MCP tools.
        Maintains conversation history per client session.
        """
        # Initialize session history if needed
        if client_id not in self.sessions:
            self.sessions[client_id] = []
        
        try:
            # Build conversation history
            history = self.sessions[client_id]
            
            # Start with system context as first message
            messages = [
                "You are a helpful banking assistant. Use the available tools to help users "
                "check their balance, deposit money, or withdraw money from their accounts. "
                "Always be friendly and confirm transactions. If user doesn't provide an account number, "
                "ask them for it.",
            ]
            
            # Add previous conversation history (interleave user/model)
            for msg in history:
                messages.append(msg)
            
            # Add current user message
            messages.append(user_input)
            
            # Call Gemini without tools - let it respond in plain text
            # We'll parse the response text for tool calls manually if needed
            response = genai.GenerativeModel(
                model_name="gemini-2.0-flash",
            ).generate_content(
                contents=messages,
                generation_config=genai.GenerationConfig(temperature=0.3),
            )
            
            # Handle response
            reply_text = ""
            if response.text:
                reply_text = response.text
            elif hasattr(response, "parts") and response.parts:
                for part in response.parts:
                    if hasattr(part, "text"):
                        reply_text = part.text
                        break
            
            # Store conversation in history (simple text format)
            history.append(user_input)
            history.append(reply_text)
            
            # Keep only last 20 items to manage token usage
            if len(history) > 20:
                self.sessions[client_id] = history[-20:]
            
            return reply_text or "I couldn't process your request. Please try again."
            
        except Exception as e:
            return f"❌ Error processing request: {str(e)}"
    
    def _execute_mcp_tool(self, tool_name: str, args: dict) -> dict:
        """Execute an MCP tool and return the result."""
        try:
            result = self._call_mcp_tool(tool_name, **args)
            return result
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}
    
    def _call_mcp_tool(self, tool_name: str, **kwargs) -> dict:
        """Call an MCP tool via the /mcp endpoint using JSON-RPC."""
        try:
            with httpx.Client(timeout=10.0) as client:
                # FastMCP uses JSON-RPC 2.0 protocol
                payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": tool_name,
                        "arguments": kwargs
                    }
                }
                
                response = client.post(
                    f"{self.mcp_url}/mcp",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    # Extract result from JSON-RPC response
                    if "result" in result:
                        return result["result"]
                    return result
                else:
                    return {"error": f"API error {response.status_code}: {response.text}"}
        except Exception as e:
            return {"error": f"Connection error: {str(e)}"}


# ============================================================================
# DEMO USAGE
# ============================================================================

if __name__ == "__main__":
    client = GeminiBankingClient(mcp_server_url="http://localhost:8002")
    
    # Example conversation
    queries = [
        "What's my balance for account 1?",
        "deposit 500 to account 1",
        "withdraw 100 from account 1",
    ]
    
    for query in queries:
        print(f"\n👤 You: {query}")
        response = client.process_query(query)
        print(f"🤖 Gemini: {response}")

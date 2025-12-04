# UNK029 Banking App - System Architecture

## Table of Contents
1. [Overview](#overview)
2. [What is FastMCP?](#what-is-fastmcp)
3. [Services](#services)
4. [Data Flow](#data-flow)
5. [FastAPI + FastMCP Integration](#fastapi--fastmcp-integration)
6. [Service Specifications](#service-specifications)
7. [Request-Response Examples](#request-response-examples)

---

## What is FastMCP?

### FastMCP Overview

**FastMCP** is a Python library that wraps FastAPI applications with the **Model Context Protocol (MCP)**, enabling AI agents to discover and call tools in a standardized way.

#### What is MCP (Model Context Protocol)?

The **Model Context Protocol** is an open standard for AI agents to:
- Discover available tools
- Call tools with structured inputs
- Receive structured outputs
- Maintain tool context and documentation

Think of it as a standardized interface between AI systems and external tools.

#### FastMCP Benefits

```
┌─────────────────────────────────┐
│    Traditional REST API         │
│  (Direct HTTP Calls)            │
├─────────────────────────────────┤
│ GET /endpoint?param=value       │
│ POST /endpoint {json}           │
│ PATCH /endpoint {json}          │
│                                 │
│ ❌ AI has to parse endpoints    │
│ ❌ Manual tool discovery        │
│ ❌ No standardized format       │
└─────────────────────────────────┘

        vs.

┌─────────────────────────────────┐
│    FastMCP with Tools           │
│  (Standardized Tool Protocol)   │
├─────────────────────────────────┤
│ Tool: get_account_tool          │
│   Input: account_no (int)       │
│   Output: account data          │
│                                 │
│ Tool: topup_account_tool        │
│   Input: account_no, amount     │
│   Output: new balance           │
│                                 │
│ ✅ AI discovers tools auto      │
│ ✅ Structured inputs/outputs    │
│ ✅ Tool documentation           │
│ ✅ Standard protocol            │
└─────────────────────────────────┘
```

### How FastMCP Works

#### Step 1: Define Tools
```python
from fastmcp import FastMCP

mcp = FastMCP("My Banking Server")

@mcp.tool()
def get_account_tool(account_no: int) -> dict:
    """Get account information"""
    return {"account_no": 1, "name": "John", "balance": 1000}

@mcp.tool()
def topup_account_tool(account_no: int, amount: float) -> dict:
    """Deposit funds into account"""
    return {"success": True, "new_balance": 1100}
```

#### Step 2: Mount on FastAPI
```python
fastapi_app = FastAPI()  # Your existing FastAPI app
mcp = FastMCP("Banking Server")  # Create MCP server

# Define tools...

# Mount both on same port
app = FastAPI()
app.mount("/", fastapi_app)          # FastAPI at /
app.mount("/mcp", mcp.http_app())    # MCP at /mcp
```

#### Step 3: AI Agent Discovers Tools
```
AI Agent connects to http://server:8002/mcp
    ↓
MCP Server responds with tool list:
  - get_account_tool
  - topup_account_tool
  - withdraw_account_tool
    ↓
AI Agent calls: topup_account_tool(account_no=1, amount=100)
    ↓
MCP Server executes tool, returns result
```

### FastMCP in UNK029 Architecture

In our banking app, **FastMCP is used to:**

1. **Expose Banking Tools** - Make banking operations available to AI agents
2. **Standardize Tool Interface** - Structured inputs/outputs for all tools
3. **Enable Tool Discovery** - AI agent automatically discovers available tools
4. **Provide Documentation** - Tool descriptions and parameters are self-documenting
5. **Validate Inputs** - Type hints and schemas validate tool parameters

```python
# mcpserver.py - FastMCP in action

from fastmcp import FastMCP
from unk029.fastapi import app as fastapi_app

# Create MCP server
mcp = FastMCP("UNK029 Bank MCP Server")

# Define banking tools
@mcp.tool()
def get_account_tool(account_no: int) -> dict:
    """Get account information (balance, name, account number)"""
    # Tool implementation
    return {"success": True, "data": {...}}

@mcp.tool()
def topup_account_tool(account_no: int, amount: float) -> dict:
    """Deposit funds into an account"""
    # Tool implementation
    return {"success": True, "data": {...}}

@mcp.tool()
def withdraw_account_tool(account_no: int, amount: float) -> dict:
    """Withdraw funds from an account"""
    # Tool implementation
    return {"success": True, "data": {...}}

# Mount FastAPI + MCP on same port (8002)
app = FastAPI()
app.mount("/", fastapi_app)           # Endpoints at / (GET, POST, PATCH)
app.mount("/mcp", mcp.http_app())     # Tools at /mcp (tool discovery & calling)
```

### FastMCP Key Features

| Feature | Description | Benefit |
|---------|-------------|---------|
| **Tool Definition** | `@mcp.tool()` decorator | Simple, declarative tool definition |
| **Auto Discovery** | Tools are self-documenting | AI doesn't need hardcoded endpoint knowledge |
| **Type Hints** | Parameters have types | Input validation and schema generation |
| **Structured Output** | Tools return dicts/objects | Consistent response format |
| **Documentation** | Docstrings become tool docs | AI understands what each tool does |
| **Error Handling** | Standard error responses | AI can handle failures gracefully |
| **Mounting** | Works with FastAPI | Combine REST API with tool protocol |

### MCP Protocol Basics

#### Tool Discovery
```
Client Request:
  GET /mcp/tools

Server Response:
  {
    "tools": [
      {
        "name": "get_account_tool",
        "description": "Get account information (balance, name, account number)",
        "inputSchema": {
          "type": "object",
          "properties": {
            "account_no": {"type": "integer"}
          },
          "required": ["account_no"]
        }
      },
      {
        "name": "topup_account_tool",
        "description": "Deposit funds into an account",
        "inputSchema": {
          "type": "object",
          "properties": {
            "account_no": {"type": "integer"},
            "amount": {"type": "number"}
          },
          "required": ["account_no", "amount"]
        }
      },
      ...
    ]
  }
```

#### Tool Calling
```
Client Request:
  POST /mcp/call
  {
    "tool_name": "topup_account_tool",
    "arguments": {
      "account_no": 1,
      "amount": 100
    }
  }

Server Response:
  {
    "success": true,
    "data": {
      "account_no": 1,
      "name": "John Doe",
      "amount_deposited": 100,
      "new_balance": 1100,
      "currency": "GBP"
    }
  }
```

### FastMCP vs Direct HTTP

#### Without FastMCP (Direct HTTP)
```python
# AI Agent has to know all endpoints
response = httpx.get("http://mcp_server:8002/account/1")
# Parse response manually
account = response.json()
balance = account["balance"]
```

**Problems:**
- ❌ No tool discovery - hardcoded endpoints
- ❌ Manual endpoint management
- ❌ No standardized format
- ❌ Error handling varies per endpoint

#### With FastMCP
```python
# AI Agent discovers tools automatically
tools = client.get_tools()  # Returns all available tools
result = client.call_tool("topup_account_tool", {
    "account_no": 1,
    "amount": 100
})
new_balance = result["data"]["new_balance"]
```

**Advantages:**
- ✅ Automatic tool discovery
- ✅ Standardized tool interface
- ✅ Type-safe parameters
- ✅ Consistent error handling
- ✅ Self-documenting

### Why FastMCP in Our Architecture?

Our banking app uses FastMCP because:

1. **AI Agent Integration** - Tools are designed for AI agents to call
2. **Tool Discovery** - Agent automatically discovers available banking tools
3. **Standardization** - All tools follow same interface (inputs, outputs, errors)
4. **Documentation** - Tool descriptions help AI understand what's available
5. **Scalability** - Easy to add new tools without changing agent code
6. **Security** - Validation and error handling at tool level

---

## Overview

The UNK029 Banking Application is built using a microservices architecture with three independent services:

- **FastAPI Service** (Port 8001): Pure banking API with database operations
- **FastMCP Server** (Port 8002): MCP tools wrapper with business logic and validation
- **AI Agent Service** (Port 8003): Natural language chat interface with Gemini AI

All services run in Docker containers orchestrated by docker-compose, with nginx as a reverse proxy on port 80/443.

---

## Services

### 1. FastAPI Service (Port 8001)
**File:** `src/unk029/fastapi.py`

#### Purpose
Pure banking API service that handles direct account operations and database interactions.

#### Responsibilities
- Account CRUD operations
- Direct deposit/withdrawal processing
- Database transaction handling

#### Endpoints

| Method | Endpoint | Description | Request | Response |
|--------|----------|-------------|---------|----------|
| GET | `/account/{account_no}` | Retrieve account details | - | `{account_no, name, balance}` |
| POST | `/account` | Create new account | `{name, balance}` | `{account_no, name, balance}` |
| PATCH | `/account/{account_no}/topup` | Deposit funds | `{amount}` | `{account_no, name, balance}` |
| PATCH | `/account/{account_no}/withdraw` | Withdraw funds | `{amount}` | `{account_no, name, balance}` |

#### Code Structure
```python
from fastapi import FastAPI
from unk029 import accounts

app = FastAPI(title="UNK029 Bank API")

@app.get("/account/{account_no}")
def get_account(account_no: int):
    return accounts.get_account(account_no)

@app.patch("/account/{account_no}/topup")
def topup_account(account_no: int, topup: accounts.TopUp):
    return accounts.topup_account(account_no, topup)

@app.patch("/account/{account_no}/withdraw")
def withdraw_account(account_no: int, withdraw: accounts.WithDraw):
    return accounts.withdraw_account(account_no, withdraw)
```

#### Key Features
- ✅ No AI logic
- ✅ No validation (delegates to MCP server)
- ✅ Pure data operations
- ✅ Reusable REST API

---

### 2. FastMCP Server (Port 8002)
**File:** `src/unk029/mcpserver.py`

#### Purpose
MCP (Model Context Protocol) server that exposes banking tools with validation and business logic. It wraps the FastAPI service and adds a tool layer for AI agents.

#### Responsibilities
- Import and mount FastAPI application
- Define MCP tools for banking operations
- Validate all business logic
- Expose both FastAPI endpoints and MCP tools
- Provide health check

#### Architecture

```
┌─────────────────────────────────────┐
│   FastMCP Server (Port 8002)        │
├─────────────────────────────────────┤
│  MCP Tools Layer                    │
│  ├─ get_account_tool()              │
│  ├─ topup_account_tool()            │
│  └─ withdraw_account_tool()         │
├─────────────────────────────────────┤
│  FastAPI Mount ("/")                │
│  ├─ GET /account/{account_no}       │
│  ├─ PATCH /account/{account_no}/... │
└─────────────────────────────────────┘
```

#### MCP Tools

##### Tool 1: get_account_tool()
**Purpose:** Retrieve account information via MCP protocol

**Parameters:**
- `account_no` (int): Account number to retrieve

**Returns:**
```json
{
  "success": true,
  "data": {
    "account_no": 1,
    "name": "John Doe",
    "balance": 1000.00,
    "currency": "GBP"
  }
}
```

**Validation:**
- ✅ Verify account exists
- ✅ Return success/error response

---

##### Tool 2: topup_account_tool()
**Purpose:** Deposit funds into an account via MCP protocol

**Parameters:**
- `account_no` (int): Account number
- `amount` (float): Amount to deposit

**Returns:**
```json
{
  "success": true,
  "data": {
    "account_no": 1,
    "name": "John Doe",
    "amount_deposited": 100.00,
    "new_balance": 1100.00,
    "currency": "GBP"
  }
}
```

**Validation:**
- ✅ Account exists
- ✅ Amount > 0
- ✅ Process topup
- ✅ Return new balance

---

##### Tool 3: withdraw_account_tool()
**Purpose:** Withdraw funds from an account via MCP protocol

**Parameters:**
- `account_no` (int): Account number
- `amount` (float): Amount to withdraw

**Returns:**
```json
{
  "success": true,
  "data": {
    "account_no": 1,
    "name": "John Doe",
    "amount_withdrawn": 100.00,
    "new_balance": 900.00,
    "currency": "GBP"
  }
}
```

**Error Response (Insufficient Funds):**
```json
{
  "success": false,
  "error": "Insufficient funds. Current balance: £1000.00, requested: £2000.00"
}
```

**Validation:**
- ✅ Account exists
- ✅ Sufficient funds available
- ✅ Amount > 0
- ✅ Process withdrawal
- ✅ Return new balance

---

#### Code Structure
```python
from fastapi import FastAPI
from fastmcp import FastMCP
from unk029.fastapi import app as fastapi_app
from unk029 import accounts

# Import FastAPI app (reuse banking endpoints)
fastapi_app = FastAPI(title="UNK029 Bank API")

# Create MCP server
mcp = FastMCP("UNK029 Bank MCP Server")

# Define MCP tools
@mcp.tool()
def get_account_tool(account_no: int) -> dict:
    """Get account information"""
    try:
        account = accounts.get_account(account_no)
        if account:
            return {
                "success": True,
                "data": {
                    "account_no": account.get("account_no"),
                    "name": account.get("name"),
                    "balance": account.get("balance"),
                    "currency": "GBP"
                }
            }
        else:
            return {"success": False, "error": f"Account #{account_no} not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool()
def topup_account_tool(account_no: int, amount: float) -> dict:
    """Deposit funds into account"""
    # Validates account exists
    # Processes topup
    # Returns success/error with new balance

@mcp.tool()
def withdraw_account_tool(account_no: int, amount: float) -> dict:
    """Withdraw funds from account"""
    # Validates account exists
    # Validates sufficient funds ⭐ KEY VALIDATION
    # Processes withdrawal
    # Returns success/error with new balance

# Mount FastAPI and MCP on same port
app = FastAPI()
app.mount("/", fastapi_app)           # Banking endpoints
app.mount("/mcp", mcp.http_app())     # MCP tools

@app.get("/health")
async def health():
    return {"status": "ok", "service": "MCP Server"}
```

#### Key Features
- ✅ All business logic and validation
- ✅ MCP tools for AI agent integration
- ✅ FastAPI endpoints for direct REST access
- ✅ Mounted on same port (8002)
- ✅ Single source of truth for banking operations

---

### 3. AI Agent Service (Port 8003)
**File:** `src/unk029/agent.py`

#### Purpose
Natural language chat interface that uses Gemini AI to understand user intent and call MCP tools for banking operations.

#### Responsibilities
- Process natural language chat messages
- Detect user intent (balance check, deposit, withdrawal)
- Extract account numbers and amounts
- Call MCP tools via HTTP
- Generate formatted responses
- Maintain conversation context

#### Architecture

```
┌──────────────────────────────────┐
│   AI Agent Service (Port 8003)   │
├──────────────────────────────────┤
│  Chat Endpoint (/chat)           │
│  ├─ Intent Detection             │
│  ├─ Entity Extraction            │
│  └─ MCP Tool Calling             │
├──────────────────────────────────┤
│  HTTP Client                     │
│  └─ Calls mcpserver:8002         │
└──────────────────────────────────┘
```

#### Main Components

##### 1. call_mcp_tool() Function
**Purpose:** HTTP wrapper to call MCP tools from mcpserver

**Function Signature:**
```python
def call_mcp_tool(tool_name: str, **kwargs) -> dict:
    """
    Call an MCP tool from the MCP server via HTTP.
    
    Args:
        tool_name: Name of the tool
        **kwargs: Tool parameters
        
    Returns:
        Response from the MCP server
    """
```

**Supported Tools:**
- `get_account_tool` - GET request to `/account/{account_no}`
- `topup_account_tool` - PATCH request to `/account/{account_no}/topup`
- `withdraw_account_tool` - PATCH request to `/account/{account_no}/withdraw`

**Example Usage:**
```python
# Check balance
result = call_mcp_tool("get_account_tool", account_no=1)

# Deposit funds
result = call_mcp_tool("topup_account_tool", account_no=1, amount=100)

# Withdraw funds
result = call_mcp_tool("withdraw_account_tool", account_no=1, amount=50)
```

---

##### 2. process_chat() Function
**Purpose:** Main chat processing with intent detection and tool calling

**Function Signature:**
```python
async def process_chat(message: str, request: Request = None) -> str:
    """
    Process user message with Gemini AI, using MCP tools for banking operations.
    
    Args:
        message: User message
        request: FastAPI request object for session management
        
    Returns:
        AI response
    """
```

**Intent Detection:**
- Balance queries: "balance", "how much", "check account"
- Deposits: "deposit", "add", "top up", "put in"
- Withdrawals: "withdraw", "take out", "remove"

**Entity Extraction:**
- Account numbers: Regex pattern `account\s*#?\s*(\d+)`
- Amounts: Regex pattern `[£$]\s*(\d+(?:\.\d{2})?)`

**Processing Flow:**
1. Extract account numbers and amounts from message
2. Detect intent keywords
3. Apply business logic based on intent
4. Call appropriate MCP tool
5. Format response with emojis and markdown
6. Return to user

**Example Response:**
```
✅ **Deposit Successful!**

Hello John! I've deposited **£100.00** into account #1.

💰 New Balance: **£1100.00**

Is there anything else I can help you with?
```

---

##### 3. Chat Endpoint
**Purpose:** FastAPI endpoint for frontend communication

**Endpoint:** `POST /chat`

**Request:**
```json
{
  "message": "Deposit £100 to account 1"
}
```

**Response:**
```json
{
  "reply": "✅ **Deposit Successful!**\n\nHello John! I've deposited **£100.00** into account #1.\n\n💰 New Balance: **£1100.00**\n\nIs there anything else I can help you with?"
}
```

---

#### Code Structure
```python
from fastapi import FastAPI, Request
from pydantic import BaseModel
import google.generativeai as genai
import httpx

app = FastAPI(title="UNK029 AI Agent - Gemini")

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

def call_mcp_tool(tool_name: str, **kwargs) -> dict:
    """Call MCP tools via HTTP"""
    with httpx.Client() as client:
        url = "http://mcp_server:8002"
        
        if tool_name == "get_account_tool":
            response = client.get(f"{url}/account/{kwargs['account_no']}")
            return response.json()
        
        elif tool_name == "topup_account_tool":
            response = client.patch(
                f"{url}/account/{kwargs['account_no']}/topup",
                json={"amount": kwargs["amount"]}
            )
            return response.json()
        
        # ... more tools

async def process_chat(message: str, request: Request = None) -> str:
    """Process user message with intent detection and tool calling"""
    # Extract intent, entities, call tools, format response
    pass

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat: ChatRequest, request: Request):
    """Main chat endpoint"""
    reply = await process_chat(chat.message, request)
    return ChatResponse(reply=reply)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "AI Agent"}
```

#### Key Features
- ✅ No database access (only calls MCP tools)
- ✅ Intent detection and entity extraction
- ✅ Conversational memory (session state)
- ✅ Fallback to Gemini AI for unknown queries
- ✅ Formatted responses with emojis
- ✅ Error handling and validation at tool level

---

## Data Flow

### Complete Request Journey

```
USER INPUT
    ↓
    ↓ "Deposit £100 to account 1"
    ↓
FRONTEND (React Chat UI)
    ↓
    ↓ POST /chat
    ↓
NGINX (Reverse Proxy)
    ↓
    ↓ Route /chat to agent:8003
    ↓
AI AGENT SERVICE (Port 8003)
    ├─ process_chat()
    ├─ Detect: is_deposit=true, account_no=1, amount=100
    └─ call_mcp_tool("topup_account_tool", account_no=1, amount=100)
        ↓
        ↓ HTTP PATCH http://mcp_server:8002/account/1/topup
        ↓
        ↓ {amount: 100}
        ↓
    FASTMCP SERVER (Port 8002)
        ├─ Receives request
        ├─ Routes to FastAPI mount point
        └─ fastapi.py handles PATCH /account/1/topup
            ├─ Validates via mcpserver tool
            ├─ Calls accounts.topup_account(1, 100)
            ├─ Returns {account_no: 1, name: "John", balance: 1100}
            ↓
            ↓ Response returned to agent
            ↓
    AI AGENT SERVICE (Port 8003)
        ├─ Receives response
        ├─ Formats: "✅ **Deposit Successful!** ... New Balance: £1100"
        └─ Returns ChatResponse to frontend
            ↓
FRONTEND
    ↓
USER SEES RESPONSE
```

---

## FastAPI + FastMCP Integration

### Why Both?

**FastAPI** provides traditional REST API functionality:
- Direct HTTP/HTTPS access
- Client libraries (JavaScript, Python, etc.)
- Web browser access
- Webhook integrations

**FastMCP** provides tool-based access:
- AI agent integration
- Tool-specific protocols
- Structured input/output
- Tool discovery and documentation

### How They Work Together

```
┌─────────────────────────────────────────────────┐
│         FastMCP Server (Port 8002)              │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌──────────────────────────────────────────┐  │
│  │         MCP Tools (@mcp.tool())          │  │
│  │                                          │  │
│  │  get_account_tool()                      │  │
│  │  topup_account_tool()                    │  │
│  │  withdraw_account_tool()                 │  │
│  └──────────────────────────────────────────┘  │
│                    ↓                            │
│  ┌──────────────────────────────────────────┐  │
│  │     Validation & Business Logic          │  │
│  │                                          │  │
│  │  ✅ Check account exists                 │  │
│  │  ✅ Validate amounts                     │  │
│  │  ✅ Check sufficient funds               │  │
│  │  ✅ Format responses                     │  │
│  └──────────────────────────────────────────┘  │
│                    ↓                            │
│  ┌──────────────────────────────────────────┐  │
│  │    Mounted FastAPI (@app.mount("/"))    │  │
│  │                                          │  │
│  │  GET /account/{account_no}               │  │
│  │  POST /account                           │  │
│  │  PATCH /account/{account_no}/topup       │  │
│  │  PATCH /account/{account_no}/withdraw    │  │
│  └──────────────────────────────────────────┘  │
│                    ↓                            │
│  ┌──────────────────────────────────────────┐  │
│  │       FastAPI App (fastapi.py)           │  │
│  │                                          │  │
│  │  Imported and mounted as-is              │  │
│  └──────────────────────────────────────────┘  │
│                    ↓                            │
│  ┌──────────────────────────────────────────┐  │
│  │       Database Layer (accounts.py)       │  │
│  │                                          │  │
│  │  Account CRUD operations                 │  │
│  │  Transaction handling                    │  │
│  └──────────────────────────────────────────┘  │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Mount Points

```python
# In mcpserver.py
app = FastAPI()
app.mount("/", fastapi_app)          # FastAPI endpoints at /
app.mount("/mcp", mcp.http_app())    # MCP protocol at /mcp
```

**Result:**
- FastAPI endpoints accessible at `http://localhost:8002/account/*`
- MCP tools accessible via MCP protocol at `http://localhost:8002/mcp`

---

## Service Specifications

### Service Comparison

| Aspect | FastAPI (8001) | FastMCP (8002) | AI Agent (8003) |
|--------|---|---|---|
| **Purpose** | Banking API | Tool wrapper | Chat interface |
| **Has Business Logic** | ❌ No | ✅ Yes | ❌ No |
| **Has Validation** | ❌ No | ✅ Yes | ❌ No |
| **Has AI/NLP** | ❌ No | ❌ No | ✅ Yes |
| **Calls Other Services** | ❌ No | ❌ No | ✅ MCP Server |
| **Direct DB Access** | ✅ Yes | ✅ Yes | ❌ No |
| **HTTP Endpoints** | ✅ Yes | ✅ Yes | ✅ Yes |
| **MCP Protocol** | ❌ No | ✅ Yes | ❌ No |

### Environment Configuration

**Docker Environment Variables:**

```yaml
# For FastAPI service
SERVICE=app

# For FastMCP service
SERVICE=mcp_server

# For AI Agent service
SERVICE=ai_agent
```

**Gemini API:**
- Required for: AI Agent (process_chat function)
- Environment variable: `GEMINI_API_KEY`

---

## Request-Response Examples

### Example 1: Check Account Balance

**User Message:**
```
"What's the balance for account 1?"
```

**Agent Processing:**
```
1. Detect: is_balance=true, account_numbers=[1]
2. Call: call_mcp_tool("get_account_tool", account_no=1)
3. HTTP: GET http://mcp_server:8002/account/1
4. MCP Server: validate account exists, return data
5. Format response with account details
```

**Response:**
```
Hello John! 👋

Your account #1 has a current balance of **£1000.00**.

Would you like to make a deposit or withdrawal?
```

---

### Example 2: Deposit Funds

**User Message:**
```
"Deposit £100 to account 1"
```

**Agent Processing:**
```
1. Detect: is_deposit=true, account_no=1, amount=100
2. Call: call_mcp_tool("topup_account_tool", account_no=1, amount=100)
3. HTTP: PATCH http://mcp_server:8002/account/1/topup
         {"amount": 100}
4. MCP Server: 
   - Validate account exists
   - Validate amount > 0
   - Call accounts.topup_account()
   - Return new balance
5. Format response with transaction details
```

**Response:**
```
✅ **Deposit Successful!**

Hello John! I've deposited **£100.00** into account #1.

💰 New Balance: **£1100.00**

Is there anything else I can help you with?
```

---

### Example 3: Insufficient Funds Withdrawal

**User Message:**
```
"Withdraw £2000 from account 1"
```

**Agent Processing:**
```
1. Detect: is_withdraw=true, account_no=1, amount=2000
2. Call: call_mcp_tool("withdraw_account_tool", account_no=1, amount=2000)
3. HTTP: PATCH http://mcp_server:8002/account/1/withdraw
         {"amount": 2000}
4. MCP Server:
   - Validate account exists ✅
   - Validate sufficient funds ❌ FAILS
   - Return error: "Insufficient funds. Current balance: £1000.00, requested: £2000.00"
5. Format error response
```

**Response:**
```
❌ Insufficient funds. Current balance: £1000.00, requested: £2000.00
```

---

## Summary

### Three-Tier Architecture

```
┌────────────────────────────────────────┐
│    Frontend (React Chat UI)            │
│    Nginx Reverse Proxy (80/443)        │
└────────────────────────────────────────┘
                   ↓
┌────────────────────────────────────────┐
│    AI Agent Service (8003)             │
│    • Gemini AI                         │
│    • Intent Detection                  │
│    • Tool Calling                      │
└────────────────────────────────────────┘
                   ↓
┌────────────────────────────────────────┐
│    FastMCP Server (8002)               │
│    • MCP Tools                         │
│    • Validation Logic                  │
│    • FastAPI Endpoints                 │
└────────────────────────────────────────┘
                   ↓
┌────────────────────────────────────────┐
│    FastAPI Service (8001)              │
│    • Database Operations               │
│    • Pure Data Layer                   │
└────────────────────────────────────────┘
```

### Key Principles

✅ **Separation of Concerns** - Each service has a single responsibility
✅ **Reusability** - Tools work with any AI implementation
✅ **Testability** - Components can be tested independently
✅ **Scalability** - Multiple AI agents can use same tool server
✅ **Security** - Validation happens at tool level
✅ **Maintainability** - Business logic in one place


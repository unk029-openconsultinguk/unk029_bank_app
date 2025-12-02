# 🏛️ UNK029 Banking Application - Complete Infrastructure Documentation

**Comprehensive guide to services, Docker, Docker Compose, and Nginx configuration**

---

## 📑 Table of Contents

1. [System Architecture Overview](#system-architecture-overview)
2. [Service 1: FastAPI Banking Server](#service-1-fastapi-banking-server)
3. [Service 2: FastMCP Server](#service-2-fastmcp-server)
4. [Service 3: AI Agent Service](#service-3-ai-agent-service)
5. [Docker Configuration](#docker-configuration)
6. [Docker Compose Setup](#docker-compose-setup)
7. [Nginx Reverse Proxy Configuration](#nginx-reverse-proxy-configuration)
8. [Request Flow & Data Pipeline](#request-flow--data-pipeline)
9. [Environment Variables](#environment-variables)
10. [Deployment & Scaling](#deployment--scaling)

---

## System Architecture Overview

### 🎯 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         NGINX REVERSE PROXY                          │
│                    (Port 80/443 → SSL/TLS)                          │
│  • Serves React frontend (static files)                             │
│  • Routes /api/account → FastAPI Service (Port 8001)               │
│  • Routes /api/chat → MCP Server (Port 8002)                       │
└────────────────┬────────────────┬─────────────────┬────────────────┘
                 │                │                 │
        ┌────────▼──────┐  ┌──────▼──────┐   ┌─────▼───────────┐
        │   FASTAPI     │  │  FASTMCP    │   │   AI AGENT      │
        │   Service     │  │   Server    │   │   (Gemini)      │
        │  (Port 8001)  │  │ (Port 8002) │   │  (Port 8003)    │
        │               │  │             │   │                 │
        │ ✅ Pure Bank  │  │ ✅ MCP Tools│   │ ✅ Gemini AI    │
        │    Operations │  │    + Fast   │   │    + MCP Client │
        │ ✅ Direct DB  │  │    API      │   │ ✅ HTTP Caller  │
        │    Access     │  │  ✅ Wraps   │   │    to MCP       │
        └────────┬──────┘  │   FastAPI   │   └─────────────────┘
                 │          │  ✅ Exposes│
                 │          │   Tools    │
                 │          └──────┬─────┘
        ┌────────▼──────────────────┘
        │
        │  (Database Connection)
        │
    ┌───▼──────────────────┐
    │  ACCOUNTS DATABASE    │
    │  (Oracle/PostgreSQL)  │
    │                       │
    │ ├─ Account Records    │
    │ ├─ Transactions       │
    │ └─ User Data          │
    └───────────────────────┘
```

### 🏗️ Three-Tier Service Architecture

| **Service** | **Port** | **Purpose** | **Responsibilities** |
|-------------|---------|-------------|----------------------|
| **FastAPI** | 8001 | Core Banking API | Database operations, account CRUD, transaction processing |
| **FastMCP** | 8002 | MCP Tools Server | Business logic, validation, tool exposure for AI agents |
| **AI Agent** | 8003 | Gemini Chat Interface | Natural language understanding, tool orchestration, conversation |

---

## Service 1: FastAPI Banking Server

### 📍 Location
```
src/unk029/fastapi.py
```

### 🎯 Purpose
**Pure banking API** - Handles all database operations and account management without business logic or validation.

### 🔧 Core Functionality

#### Endpoints Provided

```python
# GET /account/{account_no}
# Returns account details: balance, name, account number
GET /account/1
→ {
    "account_no": 1,
    "name": "John Doe",
    "balance": 5000.00,
    "currency": "GBP"
  }

# POST /account
# Creates a new account
POST /account
Body: { "name": "Jane Smith", "initial_balance": 1000 }
→ { "account_no": 2, "success": true }

# PATCH /account/{account_no}/topup
# Deposits money into account
PATCH /account/1/topup
Body: { "amount": 500 }
→ {
    "account_no": 1,
    "name": "John Doe",
    "balance": 5500.00,
    "previous_balance": 5000.00
  }

# PATCH /account/{account_no}/withdraw
# Withdraws money from account
PATCH /account/1/withdraw
Body: { "amount": 200 }
→ {
    "account_no": 1,
    "name": "John Doe",
    "balance": 5300.00,
    "previous_balance": 5500.00
  }
```

### 📦 Dependencies
- **FastAPI** - Web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation
- **accounts** module - Database operations layer

### 🚀 Startup Command
```bash
# Docker Compose automatically runs:
uvicorn src.unk029.fastapi:app --host 0.0.0.0 --port 8001
```

### 🔒 Design Principles
- ✅ **Zero validation logic** - Just pass-through to database
- ✅ **Direct database access** - No intermediate processing
- ✅ **REST endpoint exposure** - Standard HTTP API
- ✅ **Stateless operations** - No session management

---

## Service 2: FastMCP Server

### 📍 Location
```
src/unk029/mcpserver.py
```

### 🎯 Purpose
**Model Context Protocol (MCP) Tools Server** - Wraps FastAPI and exposes banking operations as standardized MCP tools for AI agents to discover and use.

### 🔧 Core Architecture

#### FastMCP Integration
```python
from fastmcp import FastMCP
from unk029.fastapi import app as fastapi_app

# Initialize MCP server
mcp = FastMCP("UNK029 Bank MCP Server")

# MCP tools decorated with @mcp.tool()
@mcp.tool()
def get_account_tool(account_no: int) -> dict:
    """Get account information"""
    # Implementation here
    pass

# Mount both FastAPI and MCP on the same port
app = FastAPI()
app.mount("/", fastapi_app)          # All /account/* endpoints
app.mount("/mcp", mcp.http_app())    # MCP tools at /mcp
```

#### ⚙️ Exposed MCP Tools

##### Tool 1: `get_account_tool`
```python
@mcp.tool()
def get_account_tool(account_no: int) -> dict:
    """
    Get account information (balance, name, account number).
    Used by AI agent to retrieve account details.
    
    Args:
        account_no: The account number
        
    Returns:
        Account details including balance, name, and account number
    """
```

**Input Schema:**
```json
{
  "account_no": 1
}
```

**Success Response:**
```json
{
  "success": true,
  "data": {
    "account_no": 1,
    "name": "John Doe",
    "balance": 5000.00,
    "currency": "GBP"
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Account #1 not found"
}
```

##### Tool 2: `topup_account_tool`
```python
@mcp.tool()
def topup_account_tool(account_no: int, amount: float) -> dict:
    """
    Deposit funds into an account.
    Validates account exists before processing.
    
    Args:
        account_no: The account number
        amount: The amount to deposit
        
    Returns:
        Success status and new balance
    """
```

**Input Schema:**
```json
{
  "account_no": 1,
  "amount": 500.00
}
```

**Success Response:**
```json
{
  "success": true,
  "data": {
    "account_no": 1,
    "name": "John Doe",
    "amount_deposited": 500.00,
    "new_balance": 5500.00,
    "currency": "GBP"
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Account #1 not found"
}
```

##### Tool 3: `withdraw_account_tool`
```python
@mcp.tool()
def withdraw_account_tool(account_no: int, amount: float) -> dict:
    """
    Withdraw funds from an account.
    Validates account exists and has sufficient funds.
    
    Args:
        account_no: The account number
        amount: The amount to withdraw
        
    Returns:
        Success status and new balance
    """
```

**Input Schema:**
```json
{
  "account_no": 1,
  "amount": 200.00
}
```

**Success Response:**
```json
{
  "success": true,
  "data": {
    "account_no": 1,
    "name": "John Doe",
    "amount_withdrawn": 200.00,
    "new_balance": 4800.00,
    "currency": "GBP"
  }
}
```

**Error Response (Insufficient Funds):**
```json
{
  "success": false,
  "error": "Insufficient funds. Current balance: £5000.00, requested: £10000.00"
}
```

### 🛡️ Validation Logic (Only Place)

FastMCP Server is the **single source of truth** for business logic:

```python
# Validation in get_account_tool
✅ Check if account exists
✅ Handle exceptions gracefully

# Validation in topup_account_tool
✅ Check if account exists
✅ Process the deposit
✅ Return structured response

# Validation in withdraw_account_tool
✅ Check if account exists
✅ Check if balance >= amount (CRITICAL)
✅ Process the withdrawal
✅ Return structured response
```

### 📦 Dependencies
- **FastMCP** - MCP protocol implementation
- **FastAPI** - HTTP wrapper
- **Uvicorn** - ASGI server
- **fastapi.py module** - Imported as `fastapi_app`
- **accounts module** - Database operations

### 🚀 Startup Command
```bash
# Docker Compose automatically runs:
uvicorn src.unk029.mcpserver:app --host 0.0.0.0 --port 8002
```

### 🔒 Design Principles
- ✅ **Tool-based exposure** - Tools are discoverable and callable
- ✅ **Unified validation** - All business logic centralized here
- ✅ **Dual endpoints** - Exposes both FastAPI (`/account/*`) and MCP tools (`/mcp`)
- ✅ **Structured responses** - All responses have `success` and `data`/`error` fields
- ✅ **Type-safe** - Input validation through type hints

---

## Service 3: AI Agent Service

### 📍 Location
```
src/unk029/agent.py
```

### 🎯 Purpose
**Conversational Banking AI** - Uses Gemini AI to understand natural language queries and call MCP tools via HTTP to process banking requests.

### 🔧 Core Architecture

#### Gemini AI Integration
```python
import google.generativeai as genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-2.5-flash")
```

#### MCP Tool Calling
```python
def call_mcp_tool(tool_name: str, **kwargs) -> dict:
    """
    Call an MCP tool from the MCP server via HTTP.
    The MCP server handles all business logic and validation.
    """
    import httpx
    
    with httpx.Client() as client:
        if tool_name == "get_account_tool":
            # GET /account/{account_no}
            response = client.get(f"http://mcp_server:8002/account/{account_no}")
            
        elif tool_name == "topup_account_tool":
            # PATCH /account/{account_no}/topup
            response = client.patch(
                f"http://mcp_server:8002/account/{account_no}/topup",
                json={"amount": amount}
            )
            
        elif tool_name == "withdraw_account_tool":
            # PATCH /account/{account_no}/withdraw
            response = client.patch(
                f"http://mcp_server:8002/account/{account_no}/withdraw",
                json={"amount": amount}
            )
            
        return response.json()
```

#### Conversational Memory
```python
session_state = {}

def _get_session_key(request: Request) -> str:
    """Get session key from client IP"""
    return request.client.host if request and request.client else "default"

def process_chat(message: str, request: Request):
    session_key = _get_session_key(request)
    
    # Retrieve conversation history
    history = session_state.get(session_key, [])
    
    # Add user message
    history.append({"role": "user", "content": message})
    
    # Send to Gemini with context
    response = model.generate_content(history)
    
    # Add response
    history.append({"role": "assistant", "content": response.text})
    
    # Save history
    session_state[session_key] = history
```

#### Chat Processing Pipeline
```
User Input (Natural Language)
    ↓
[Gemini Analysis]
    ├─ Detects intent (balance_check, deposit, withdrawal)
    ├─ Extracts entities (account_no, amount)
    └─ Decides which tool to call
    ↓
[MCP Tool Calling]
    └─ Calls appropriate HTTP endpoint on mcp_server:8002
    ↓
[Response Formatting]
    ├─ Formats tool response
    ├─ Generates conversational reply
    └─ Maintains conversation history
    ↓
Chat Response (Friendly Message)
```

### 📋 Endpoints

#### POST /chat
```bash
POST /api/chat
Content-Type: application/json

{
  "message": "What's my balance on account 1?"
}
```

**Response:**
```json
{
  "reply": "Your current balance on account 1 is £5000.00. Is there anything else I can help you with?"
}
```

### 📦 Dependencies
- **FastAPI** - Web framework
- **Uvicorn** - ASGI server
- **google-generativeai** - Gemini AI SDK
- **httpx** - HTTP client for MCP calls
- **pydantic** - Data models
- **python-dotenv** - Environment variable loading

### 🚀 Startup Command
```bash
# Docker Compose automatically runs:
uvicorn src.unk029.agent:app --host 0.0.0.0 --port 8003
```

### 🔒 Design Principles
- ✅ **Zero database access** - All data requests go through MCP
- ✅ **No validation logic** - Trusts MCP server for validation
- ✅ **Pure HTTP client** - Acts as proxy to MCP tools
- ✅ **Stateful conversations** - Maintains message history per session
- ✅ **Gemini-powered** - Uses latest Gemini 2.5 Flash model

---

## Docker Configuration

### 📍 Location
```
Dockerfile
```

### 📝 Overview

The Dockerfile uses a **multi-stage build** to optimize image size and follows Docker best practices:

1. **Builder Stage** - Compiles Python dependencies
2. **Runtime Stage** - Minimal runtime image

### 🏗️ Builder Stage (python_builder)

```dockerfile
FROM python:3.12-slim-bookworm AS python_builder

ENV UV_VERSION=0.8.8
ENV UV_PYTHON_DOWNLOADS=never
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /src

# Install uv package manager
RUN pip install "uv==${UV_VERSION}"

# Set virtual environment path
ENV UV_PROJECT_ENVIRONMENT=/opt/venv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --locked --no-default-groups --no-install-project

# Copy source code
COPY README.md ./
COPY src src

# Install project
RUN uv sync --locked --no-default-groups --no-editable
```

**Purpose:**
- Uses `uv` package manager (faster than pip)
- Pre-compiles all dependencies into wheels
- Caches layers for faster rebuilds

### 🚀 Runtime Stage

```dockerfile
FROM python:3.12-slim-bookworm

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONBUFFERED=1
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV HOME=/home/user
ENV APP_HOME=${HOME}/app
ENV SERVICE=mcp_server

# Create non-root user
RUN mkdir -p ${HOME}
RUN groupadd -r user && \
    useradd -r -g user -d ${HOME} -s /sbin/nologin -c "Container image user" user

# Setup application directory
RUN mkdir ${APP_HOME}
WORKDIR ${APP_HOME}

# Copy virtual environment from builder
COPY --from=python_builder ${UV_PROJECT_ENVIRONMENT} ${UV_PROJECT_ENVIRONMENT}
ENV PATH="${UV_PROJECT_ENVIRONMENT}/bin:${PATH}"

# Set permissions
RUN chown -R user:user ${HOME}

# Multi-service startup command
CMD ["sh", "-c", "case \"$SERVICE\" in \
  mcp_server) uvicorn src.unk029.mcpserver:app --host 0.0.0.0 --port 8002 ;; \
  ai_agent) uvicorn src.unk029.agent:app --host 0.0.0.0 --port 8003 ;; \
  app) uvicorn src.unk029.fastapi:app --host 0.0.0.0 --port 8001 ;; \
  *) echo \"Unknown service: $SERVICE\" && exit 1 ;; \
esac"]

USER user
```

### 🎯 Key Features

| Feature | Purpose |
|---------|---------|
| **Multi-stage build** | Reduces final image size (no build deps) |
| **Non-root user** | Security best practice |
| **SERVICE env var** | Routes to correct service based on Docker Compose setting |
| **Virtual environment** | Isolated Python dependencies |
| **Slim Bookworm** | Minimal base image (≈200MB vs 1GB standard) |

### 📦 Image Specifications
- **Base Image:** `python:3.12-slim-bookworm` (≈200MB)
- **Final Size:** ≈500MB (with dependencies)
- **Architecture:** Single image, multiple services via `$SERVICE`
- **Build Time:** ≈2-3 minutes first build, ≈10 seconds cached

### 🔨 Building the Image

```bash
# Build the image locally
docker build -t unk029-bank-app:latest .

# Verify image
docker images | grep unk029-bank-app
```

---

## Docker Compose Setup

### 📍 Location
```
docker-compose.yml
```

### 📝 Overview

Docker Compose orchestrates **4 services**:
1. **app** - FastAPI Banking Server (Port 8001)
2. **mcp_server** - MCP Tools Server (Port 8002)
3. **ai_agent** - AI Agent Service (Port 8003)
4. **nginx** - Reverse Proxy (Ports 80/443)

### 🎯 Complete Configuration

```yaml
version: "3.8"
services:
  # Service 1: FastAPI Banking Server
  app:
    build: .
    container_name: unk029_bank_app
    expose:
      - "8001"
    environment:
      TNS_ADMIN: /opt/oracle/wallet
    volumes:
      - ./wallet:/opt/oracle/wallet:ro
    env_file:
      - .env
    restart: unless-stopped

  # Service 2: FastMCP Server (depends on app)
  mcp_server:
    build: .
    container_name: unk029_mcp_server
    environment:
      SERVICE: mcp_server
      PORT: 8002
    env_file:
      - .env
    expose:
      - "8002"
    depends_on:
      - app
    restart: unless-stopped

  # Service 3: AI Agent (depends on mcp_server)
  ai_agent:
    build: .
    container_name: unk029_ai_agent
    environment:
      SERVICE: ai_agent
      PORT: 8003
    env_file:
      - .env
    expose:
      - "8003"
    depends_on:
      - mcp_server
    restart: unless-stopped

  # Service 4: Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: unk029_nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - ./frontend/dist:/usr/share/nginx/html:ro
      - ./env/fullchain.pem:/etc/nginx/env/fullchain.pem:ro
      - ./env/privkey.pem:/etc/nginx/env/privkey.pem:ro
    depends_on:
      - app
      - mcp_server
      - ai_agent
    restart: unless-stopped
```

### 📦 Service Details

#### Service 1: `app` (FastAPI)

```yaml
app:
  build: .                              # Use Dockerfile (default SERVICE=app)
  container_name: unk029_bank_app
  expose:
    - "8001"                            # Expose only to Docker network
  environment:
    TNS_ADMIN: /opt/oracle/wallet       # Oracle wallet location
  volumes:
    - ./wallet:/opt/oracle/wallet:ro    # Mount wallet (read-only)
  env_file:
    - .env                              # Load environment variables
  restart: unless-stopped               # Auto-restart on failure
```

**Startup Flow:**
- Dockerfile builds image with default `SERVICE=app`
- Dockerfile CMD runs: `uvicorn src.unk029.fastapi:app --host 0.0.0.0 --port 8001`
- Service available at `http://app:8001` within Docker network

**Why exposed, not published:**
- `expose` only makes ports available to other containers
- Nginx will access it as `http://app:8001` internally
- No direct external access (safer)

#### Service 2: `mcp_server` (FastMCP)

```yaml
mcp_server:
  build: .                              # Use same Dockerfile
  container_name: unk029_mcp_server
  environment:
    SERVICE: mcp_server                 # Override default SERVICE
    PORT: 8002
  env_file:
    - .env
  expose:
    - "8002"
  depends_on:
    - app                               # Must start app first
  restart: unless-stopped
```

**Startup Flow:**
- Builds same image
- Sets `SERVICE=mcp_server` environment variable
- Dockerfile CMD runs: `uvicorn src.unk029.mcpserver:app --host 0.0.0.0 --port 8002`
- Service available at `http://mcp_server:8002` within Docker network
- Can call `http://app:8001` (depends_on ensures app started first)

#### Service 3: `ai_agent` (Gemini AI)

```yaml
ai_agent:
  build: .                              # Use same Dockerfile
  container_name: unk029_ai_agent
  environment:
    SERVICE: ai_agent                   # Override default SERVICE
    PORT: 8003
    GEMINI_API_KEY: ${GEMINI_API_KEY}   # From .env file
  env_file:
    - .env
  expose:
    - "8003"
  depends_on:
    - mcp_server                        # Must start mcp_server first
  restart: unless-stopped
```

**Startup Flow:**
- Builds same image
- Sets `SERVICE=ai_agent` environment variable
- Dockerfile CMD runs: `uvicorn src.unk029.agent:app --host 0.0.0.0 --port 8003`
- Service available at `http://ai_agent:8003` within Docker network
- Can call `http://mcp_server:8002` (depends_on ensures mcp_server started first)

**Dependency Chain:**
```
app:8001
    ↑
    └─── mcp_server:8002
             ↑
             └─── ai_agent:8003
```

#### Service 4: `nginx` (Reverse Proxy)

```yaml
nginx:
  image: nginx:alpine                   # Official Nginx image
  container_name: unk029_nginx
  ports:
    - "80:80"                           # HTTP - external
    - "443:443"                         # HTTPS - external
  volumes:
    - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
    - ./frontend/dist:/usr/share/nginx/html:ro
    - ./env/fullchain.pem:/etc/nginx/env/fullchain.pem:ro
    - ./env/privkey.pem:/etc/nginx/env/privkey.pem:ro
  depends_on:
    - app
    - mcp_server
    - ai_agent
  restart: unless-stopped
```

**Volume Mounts:**
- `nginx.conf` - Routing configuration (read-only)
- `frontend/dist` - React frontend static files (read-only)
- SSL certificates for HTTPS

**Port Binding:**
- Published ports (external access)
- Can access other services via Docker DNS (`http://app:8001`, etc.)

### 🚀 Starting Services

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f app
docker-compose logs -f mcp_server
docker-compose logs -f ai_agent
docker-compose logs -f nginx

# Stop all services
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

### 🔍 Service Verification

```bash
# Check if services are running
docker-compose ps

# Test FastAPI service
curl -s http://localhost:8001/account/1 | jq

# Test Nginx proxy
curl -s http://localhost/api/account/1 | jq

# Test chat endpoint
curl -X POST http://localhost/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is my balance?"}'
```

---

## Nginx Reverse Proxy Configuration

### 📍 Location
```
nginx.conf
```

### 🎯 Purpose

Nginx acts as the **single entry point** for all traffic:
- Serves React frontend (static files)
- Routes API requests to appropriate backend services
- Handles SSL/TLS encryption
- Manages HTTP → HTTPS redirection

### 📝 Complete Configuration

```nginx
server {
    # Listen on both HTTP and HTTPS
    listen 80;
    listen 443 ssl;
    server_name unk029.dev.openconsultinguk.com;

    # SSL certificates
    ssl_certificate /etc/nginx/env/fullchain.pem;
    ssl_certificate_key /etc/nginx/env/privkey.pem;

    # Redirect HTTP to HTTPS
    if ($scheme = http) {
        return 301 https://$server_name$request_uri;
    }

    # ═══════════════════════════════════════════════════════════
    # Route 1: Frontend Static Files
    # ═══════════════════════════════════════════════════════════
    
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }


    # ═══════════════════════════════════════════════════════════
    # Route 2: Bank API - /api/account → FastAPI:8001
    # ═══════════════════════════════════════════════════════════
    
    location /api/account {
        # Rewrite /api/account/* → /account/*
        rewrite ^/api/account(.*)$ /account$1 break;
        
        proxy_pass http://app:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Direct access to /account
    location /account {
        proxy_pass http://app:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }


    # ═══════════════════════════════════════════════════════════
    # Route 3: Chat API - /api/chat → MCP Server:8002
    # ═══════════════════════════════════════════════════════════
    
    location /api/chat {
        # Rewrite /api/chat/* → /chat/*
        rewrite ^/api/chat(.*)$ /chat$1 break;
        
        proxy_pass http://mcp_server:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Direct access to /chat
    location /chat {
        proxy_pass http://mcp_server:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }


    # ═══════════════════════════════════════════════════════════
    # Route 4: MCP Tools - /mcp → MCP Server:8002
    # ═══════════════════════════════════════════════════════════
    
    location /mcp {
        proxy_pass http://mcp_server:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 🗺️ Routing Map

| **Frontend Route** | **Backend Target** | **Purpose** |
|---|---|---|
| `GET /` | React SPA (static) | Main application |
| `GET /api/account/{id}` | `app:8001/account/{id}` | Get account details |
| `POST /api/account` | `app:8001/account` | Create account |
| `PATCH /api/account/{id}/topup` | `app:8001/account/{id}/topup` | Deposit funds |
| `PATCH /api/account/{id}/withdraw` | `app:8001/account/{id}/withdraw` | Withdraw funds |
| `POST /api/chat` | `mcp_server:8002/chat` | Send chat message |
| `/mcp` | `mcp_server:8002/mcp` | MCP protocol access |

### 🔄 Request Flow Examples

#### Example 1: Get Account Balance
```
User Browser: GET https://unk029.dev.openconsultinguk.com/api/account/1
     ↓
Nginx (HTTPS → HTTP):
  Rewrites: /api/account/1 → /account/1
  Routes to: http://app:8001/account/1
     ↓
FastAPI (Port 8001):
  @app.get("/account/{account_no}")
  Returns: {"account_no": 1, "name": "John", "balance": 5000}
     ↓
Nginx (HTTP → HTTPS):
  Returns to browser with SSL wrapper
     ↓
User Browser: Receives response
```

#### Example 2: Chat Request
```
User Browser: POST https://unk029.dev.openconsultinguk.com/api/chat
  Body: {"message": "What's my balance?"}
     ↓
Nginx (HTTPS → HTTP):
  Rewrites: /api/chat → /chat
  Routes to: http://mcp_server:8002/chat
     ↓
MCP Server (Port 8002):
  @app.post("/chat")
  Calls Gemini AI
  Calls MCP tools via agent
  Returns formatted response
     ↓
Nginx (HTTP → HTTPS):
  Returns to browser with SSL wrapper
     ↓
User Browser: Receives chat response
```

### 🔒 Security Features

| Feature | Implementation |
|---------|---|
| **HTTP → HTTPS** | `if ($scheme = http) return 301` - All traffic encrypted |
| **Header Forwarding** | `X-Real-IP`, `X-Forwarded-For`, `X-Forwarded-Proto` - Service knows real client |
| **Read-only volumes** | `:ro` flag - Config and certs cannot be modified |
| **Non-root user** | Both app and nginx run as non-root |
| **URL Rewriting** | Internal routing hidden from client |

### 🚀 SSL/TLS Configuration

**Certificate Files Required:**
```bash
env/fullchain.pem      # Full certificate chain (public key)
env/privkey.pem        # Private key (SECRET - protect this!)
```

**SSL Directives:**
```nginx
listen 443 ssl;
ssl_certificate /etc/nginx/env/fullchain.pem;
ssl_certificate_key /etc/nginx/env/privkey.pem;
```

**HTTP to HTTPS Redirect:**
```nginx
if ($scheme = http) {
    return 301 https://$server_name$request_uri;
}
```

---

## Request Flow & Data Pipeline

### 🔀 Complete Request Lifecycle

```
╔═══════════════════════════════════════════════════════════════════════════╗
║                    USER REQUEST LIFECYCLE                                 ║
╚═══════════════════════════════════════════════════════════════════════════╝

1️⃣  USER SENDS REQUEST
    └─ Browser: POST /api/chat
       Body: {"message": "Deposit £500 to account 1"}

2️⃣  HTTPS ENCRYPTION
    └─ TLS/SSL handshake
       Client sends encrypted request

3️⃣  NGINX RECEIVES (Port 443)
    └─ Listens on 443 (SSL)
    └─ Decrypts request
    └─ Checks route matching

4️⃣  NGINX REWRITES & ROUTES
    └─ Request: POST /api/chat
    └─ Rewrites to: POST /chat
    └─ Routes to: http://mcp_server:8002

5️⃣  MCP SERVER RECEIVES (Port 8002)
    └─ @app.post("/chat")
    └─ Receives: {"message": "Deposit £500 to account 1"}
    └─ Session key: client IP

6️⃣  GEMINI AI ANALYZES
    └─ Input: User message
    └─ Processing:
       ├─ Intent detection: is_deposit = True
       ├─ Entity extraction: account_no = 1, amount = 500
       └─ Tool selection: topup_account_tool
    └─ Calls: call_mcp_tool("topup_account_tool", ...)

7️⃣  AI AGENT MAKES HTTP CALL
    └─ Service: ai_agent:8003
    └─ Calls: PATCH http://mcp_server:8002/account/1/topup
    └─ Body: {"amount": 500}

8️⃣  MCP SERVER VALIDATES & EXECUTES
    └─ @mcp.tool() topup_account_tool()
    └─ Validation:
       ├─ ✅ Check account exists
       ├─ ✅ Check amount > 0
       └─ ✅ All validations pass
    └─ Calls: accounts.topup_account(1, TopUp(amount=500))

9️⃣  FASTAPI EXECUTES DATABASE OP
    └─ Service: app:8001
    └─ Updates database
    └─ Returns: {"name": "John", "balance": 5500}

🔟 MCP SERVER FORMATS RESPONSE
    └─ Success response:
       {
         "success": true,
         "data": {
           "account_no": 1,
           "name": "John",
           "amount_deposited": 500,
           "new_balance": 5500,
           "currency": "GBP"
         }
       }

1️⃣1️⃣ AI AGENT FORMATS CHAT RESPONSE
    └─ Generates natural language:
       "✅ Deposit Successful! I've deposited £500 to account 1.
        Your new balance is £5500.00."
    └─ Returns: {"reply": "...message..."}

1️⃣2️⃣ MCP SERVER RETURNS TO NGINX
    └─ HTTP Response to nginx proxy

1️⃣3️⃣ NGINX ENCRYPTS & RETURNS
    └─ Encrypts response with SSL
    └─ Sends to browser

1️⃣4️⃣ BROWSER RENDERS
    └─ Displays message to user
    └─ UI shows: ✅ Deposit Successful!
```

### 📊 Service Interaction Diagram

```
┌────────────────┐
│ React Frontend │
│   (Browser)    │
└────────┬───────┘
         │
         │ HTTPS Request
         │ /api/chat
         ▼
┌────────────────────────────────┐
│  NGINX Reverse Proxy           │
│  (Port 80/443)                 │
│  ├─ Routes /api/chat → mcp     │
│  ├─ Routes /api/account → app  │
│  └─ Serves static files        │
└────┬──────────────┬────────┬───┘
     │              │        │
     │ HTTP         │ HTTP   │ HTTP
     │ /account     │ /chat  │ /mcp
     ▼              ▼        ▼
  ┌──────────┐  ┌──────────────┐
  │ FastAPI  │  │ FastMCP      │
  │ :8001    │  │ Server       │
  │          │  │ :8002        │
  │ Pure     │  │              │
  │ Banking  │  │ ├─ MCP Tools │
  │ API      │  │ ├─ FastAPI   │
  │ ✅ DB    │  │ │  wrapper   │
  │  Access  │  │ ├─ Validation│
  │          │  │ └─ Structures│
  └────┬─────┘  └──────┬───────┘
       │               │
       │ HTTP          │ HTTP
       │ /account      │ /account
       │               │
       ▼               ▼
     ┌──────────────────────┐
     │  AI Agent :8003      │
     │                      │
     │ ├─ Gemini AI         │
     │ ├─ MCP Client        │
     │ ├─ HTTP Caller       │
     │ └─ Chat Logic        │
     └──────────┬───────────┘
                │
         HTTP to MCP Server
                │
                ▼ (via Docker network)
          ┌──────────────┐
          │  Database    │
          │  (Oracle)    │
          │              │
          │ ├─ Accounts  │
          │ ├─ Balances  │
          │ └─ Txn Log   │
          └──────────────┘
```

### 🔍 Data Transformation Examples

#### Example: Deposit Request

**User Input (Natural Language):**
```
"Deposit £500 to account 1"
```

**AI Analysis → Tool Call:**
```json
{
  "intent": "deposit",
  "account_no": 1,
  "amount": 500.00,
  "tool": "topup_account_tool"
}
```

**HTTP Request to MCP:**
```http
PATCH /account/1/topup HTTP/1.1
Host: mcp_server:8002
Content-Type: application/json

{
  "amount": 500
}
```

**Database Update:**
```sql
UPDATE accounts
SET balance = balance + 500
WHERE account_no = 1
```

**Tool Response:**
```json
{
  "success": true,
  "data": {
    "account_no": 1,
    "name": "John Doe",
    "amount_deposited": 500,
    "new_balance": 5500,
    "currency": "GBP"
  }
}
```

**Chat Response to User:**
```
"✅ Deposit Successful! I've deposited £500 to account 1.
Your new balance is now £5500.00. Is there anything else I can help you with?"
```

---

## Environment Variables

### 📝 `.env` File Configuration

```bash
# ═══════════════════════════════════════════════════════════
# GEMINI AI CONFIGURATION
# ═══════════════════════════════════════════════════════════

GEMINI_API_KEY=your_gemini_api_key_here

# ═══════════════════════════════════════════════════════════
# DATABASE CONFIGURATION
# ═══════════════════════════════════════════════════════════

# Oracle Database
DB_HOST=your_oracle_host
DB_PORT=1521
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_SERVICE=your_oracle_service

# Or PostgreSQL (if using)
# DATABASE_URL=postgresql://user:password@localhost/unk029

# ═══════════════════════════════════════════════════════════
# APPLICATION CONFIGURATION
# ═══════════════════════════════════════════════════════════

APP_NAME=UNK029 Banking Application
ENVIRONMENT=production

# ═══════════════════════════════════════════════════════════
# SERVICE PORTS (used by docker-compose)
# ═══════════════════════════════════════════════════════════

# FastAPI Port
FASTAPI_PORT=8001

# MCP Server Port
MCP_SERVER_PORT=8002

# AI Agent Port
AI_AGENT_PORT=8003

# ═══════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════

LOG_LEVEL=info
```

### 📋 Environment Variable Usage in Services

**FastAPI Service:**
```python
# src/unk029/fastapi.py
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
# Initializes database connection
```

**MCP Server:**
```python
# src/unk029/mcpserver.py
# Inherits database config from FastAPI
```

**AI Agent:**
```python
# src/unk029/agent.py
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)
```

**Docker Compose:**
```yaml
services:
  app:
    env_file:
      - .env
  mcp_server:
    env_file:
      - .env
  ai_agent:
    env_file:
      - .env
```

### 🔒 Security Best Practices

✅ **DO:**
- Store `.env` in `.gitignore`
- Use strong, unique API keys
- Rotate keys regularly
- Use different keys for dev/prod
- Store secrets in secure vault (production)

❌ **DON'T:**
- Commit `.env` to Git
- Log API keys
- Share `.env` via email/Slack
- Use same key everywhere
- Expose secrets in Docker build args

---

## Deployment & Scaling

### 🚀 Local Development

```bash
# 1. Clone repository
git clone <repo>
cd unk029_bank_app

# 2. Create .env file
cp .env.example .env
# Edit .env with your API keys and DB credentials

# 3. Start all services
docker-compose up -d

# 4. Verify services
docker-compose ps

# 5. Test endpoints
curl http://localhost/api/account/1
curl -X POST http://localhost/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'

# 6. View logs
docker-compose logs -f
```

### 🐳 Production Deployment

#### Prerequisites
- Docker & Docker Compose installed
- SSL certificates (fullchain.pem, privkey.pem)
- Database configured and accessible
- Gemini API key

#### Deployment Steps

```bash
# 1. Prepare environment
mkdir -p env
cp fullchain.pem env/
cp privkey.pem env/
chmod 600 env/privkey.pem

# 2. Configure .env
nano .env
# Set production database credentials
# Set production API keys
# Set ENVIRONMENT=production

# 3. Build images
docker-compose build

# 4. Start services
docker-compose up -d

# 5. Verify deployment
docker-compose ps
docker-compose logs -f nginx

# 6. Health checks
curl https://unk029.dev.openconsultinguk.com/api/account/1
curl https://unk029.dev.openconsultinguk.com/
```

### 📈 Scaling Considerations

#### Horizontal Scaling (Multiple Instances)

```yaml
# Scale MCP servers for high concurrency
mcp_server_1:
  build: .
  container_name: unk029_mcp_server_1
  environment:
    SERVICE: mcp_server
  
mcp_server_2:
  build: .
  container_name: unk029_mcp_server_2
  environment:
    SERVICE: mcp_server

# Nginx load balancing
upstream mcp_servers {
  server mcp_server_1:8002;
  server mcp_server_2:8002;
}

location /chat {
  proxy_pass http://mcp_servers;
}
```

#### Vertical Scaling (More Resources)

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
```

#### Database Connection Pooling

```python
# In accounts module
from sqlalchemy import create_engine

engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

### 🔄 Monitoring & Maintenance

#### Health Checks

```bash
# Check all services running
docker-compose ps

# Check service logs
docker-compose logs app
docker-compose logs mcp_server
docker-compose logs ai_agent
docker-compose logs nginx

# Test endpoints
curl http://localhost:8001/account/1
curl http://localhost:8002/account/1
curl http://localhost:8003/chat

# Monitor resource usage
docker stats
```

#### Restart Policies

```yaml
# Auto-restart on failure
restart: unless-stopped

# Restart only if not manually stopped
restart: always

# Don't auto-restart
restart: "no"
```

#### Log Rotation

```yaml
services:
  app:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 🆘 Troubleshooting

#### Service Won't Start

```bash
# Check logs
docker-compose logs service_name

# Rebuild image
docker-compose build service_name

# Force restart
docker-compose restart service_name
```

#### Port Already in Use

```bash
# Find process using port
lsof -i :80
lsof -i :443

# Kill process
kill -9 <PID>

# Or use different ports in docker-compose
ports:
  - "8080:80"
  - "8443:443"
```

#### Database Connection Issues

```bash
# Test database connection
docker-compose exec app python -c \
  "from unk029 import accounts; print(accounts.get_account(1))"

# Check env variables
docker-compose exec app env | grep DB
```

#### SSL Certificate Issues

```bash
# Verify certificate
openssl x509 -in env/fullchain.pem -text -noout

# Check certificate validity
openssl x509 -in env/fullchain.pem -noout -dates

# Reload Nginx (picks up new certs)
docker-compose exec nginx nginx -s reload
```

---

## Summary Table

### Services Comparison

| **Aspect** | **FastAPI (8001)** | **FastMCP (8002)** | **AI Agent (8003)** | **Nginx** |
|---|---|---|---|---|
| **Purpose** | Banking API | Tool Wrapper | Chat Interface | Reverse Proxy |
| **Role** | Database Access | Tool Exposure | User Interaction | Traffic Router |
| **Validation** | None | ✅ Full | None | None |
| **Business Logic** | None | ✅ Tools | Conversation | Routing |
| **Database Access** | ✅ Direct | ✅ Indirect | ❌ None | ❌ None |
| **Listens On** | 8001 | 8002 | 8003 | 80/443 |
| **Exposes** | REST API | MCP Tools + REST | Chat API | Web/APIs |
| **Upstream Calls** | Database | FastAPI:8001 | MCP:8002 | All services |
| **Restart Policy** | unless-stopped | unless-stopped | unless-stopped | unless-stopped |

### Request Routing Summary

| **Request** | **Route** | **Handler** |
|---|---|---|
| `GET /` | Static Files | Nginx (React) |
| `GET /api/account/1` | `/api/account` | Nginx → FastAPI:8001 |
| `POST /api/account` | `/api/account` | Nginx → FastAPI:8001 |
| `PATCH /api/account/1/topup` | `/api/account` | Nginx → FastAPI:8001 |
| `POST /api/chat` | `/api/chat` | Nginx → MCP:8002 → AI Agent:8003 |
| `GET /mcp` | `/mcp` | Nginx → MCP:8002 |

---

**Document Version:** 1.0  
**Last Updated:** November 29, 2025  
**Maintained By:** UNK029 Development Team

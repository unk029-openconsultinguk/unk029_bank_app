# UNK029 Bank - AI-Powered Banking Interface

A complete full-stack banking application with AI chat integration using React, TypeScript, FastAPI, Google Gemini AI, and Model Context Protocol (MCP).

## 🏗️ Architecture

```
┌─────────────────┐
│  React Frontend │ 
│  TypeScript/Vite│
└────────┬────────┘
         │
    ┌────▼────┐
    │  Nginx  │ (Ports 80/443/8080)
    │ Proxy   │
    └────┬────┘
         │
    ┌────┴──────────────────────┐
    │                           │
┌───▼──────┐          ┌─────────▼────────┐
│ FastAPI  │          │   MCP Server     │
│ Bank API │          │  + Gemini AI     │
│(Port 8001)│          │   (Port 8002)    │
└────┬─────┘          └─────────┬────────┘
     │                          │
┌────▼─────┐          ┌─────────▼────────┐
│ Oracle   │          │  Google Gemini   │
│   DB     │          │   AI (2.5-flash) │
└──────────┘          └──────────────────┘
```

## 🚀 Quick Start

### 1. Build Frontend
```bash
cd frontend
npm install
npm run build
chmod -R 755 dist
cd ..
```

### 2. Start All Services
```bash
docker compose up --build -d
```

### 3. Access Application
- **Frontend UI**: http://localhost:8080
- **Chat with AI**: http://localhost:8080/chat
- **Bank API**: http://localhost:8080/account

## 🎨 Features

### AI Chat Interface
- Real-time chat with Google Gemini AI
- Typing indicators & smooth animations
- Message history with avatars
- Natural language banking queries

### Account Management
- Create accounts with initial balance
- View account details
- Deposit & withdraw funds
- Real-time balance updates

## 📝 API Endpoints

### Bank Operations
```bash
# Create Account
POST /account
{"name": "John Doe", "balance": 1000.00}

# Get Account
GET /account/{account_no}

# Deposit
PATCH /account/{account_no}/topup
{"amount": 500.00}

# Withdraw
PATCH /account/{account_no}/withdraw
{"amount": 200.00}
```

### AI Chat
```bash
# Chat with Gemini
POST /chat
{"message": "What is my balance?"}
```

## 🔧 Development

### Run Frontend Locally
```bash
cd frontend
npm run dev
# Access at http://localhost:3000
```

### View Logs
```bash
docker logs -f unk029_nginx       # Nginx proxy
docker logs -f unk029_bank_app    # Bank API
docker logs -f unk029_mcp_server  # AI Chat
```

### Rebuild After Changes
```bash
# Frontend changes
cd frontend && npm run build && cd ..
docker compose restart nginx

# Backend changes
docker compose up --build -d
```

## 🛠️ Technology Stack

- **Frontend**: React 18, TypeScript, Vite
- **Backend**: FastAPI, FastMCP, Python 3.12
- **AI**: Google Gemini 2.5 Flash
- **Database**: Oracle Autonomous DB
- **Infrastructure**: Docker, Nginx, SSL

## ✅ What's Working

✅ React frontend with modern UI  
✅ AI chat with Gemini 2.5 Flash  
✅ Account CRUD operations  
✅ Nginx reverse proxy  
✅ Docker orchestration  
✅ MCP protocol integration  
✅ SSL/TLS support  

## 📄 License

MIT

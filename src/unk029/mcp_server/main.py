"""
MCP Server Entry Point
Imports and runs the MCP server from src/unk029/mcpserver.py
"""

import sys
import os

# Add parent directory to path so we can import unk029 modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcpserver import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

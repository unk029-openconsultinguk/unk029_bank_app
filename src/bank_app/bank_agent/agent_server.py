# agent_server.py
import os
import logging
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn

logger = logging.getLogger(__name__)

# Try to import Google ADK
try:
    from google.adk.cli.fast_api import get_fast_api_app
    ADK_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Google ADK not available: {e}")
    ADK_AVAILABLE = False

if ADK_AVAILABLE:
    # Create a FastAPI app from the ADK package pointing at local agents directory.
    app: FastAPI = get_fast_api_app(
        agents_dir="./src/bank_app",
        web=False,
        a2a=False,
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8004)),
        allow_origins=["*"],
        url_prefix=None,
    )
    logger.info("Agent server initialized with Google ADK")
else:
    # Create a stub FastAPI app that returns a message
    app = FastAPI(title="UNK029 Agent Server - Unavailable")
    
    @app.get("/")
    async def root():
        return JSONResponse(
            status_code=503,
            content={
                "error": "Google ADK not available",
                "message": "The agent server requires google-adk package which is not yet available. Install a working version of google-adk to enable this feature."
            }
        )
    
    @app.get("/health")
    async def health():
        return {"status": "degraded", "reason": "google-adk not available"}
    
    logger.warning("Agent server running in stub mode - Google ADK not available")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8004)))

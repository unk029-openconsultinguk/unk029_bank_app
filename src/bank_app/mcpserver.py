"""Minimal MCP Server wrapping FastAPI banking endpoints into a single tool."""

import logging
import os
from typing import Any

from fastapi import FastAPI
from fastmcp import FastMCP

import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Bank MCP Server")
mcp = FastMCP("Bank MCP")

BANK_API = os.getenv("BANK_API_URL", "http://unk029_bank_app:8001")


@mcp.tool()
def UNK029_Bank(action: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Perform banking actions via the FastAPI backend.

    Actions:
    - get_account: payload {account_no}
    - transfer: payload {from_account_no, to_account_no, amount}
    - topup: payload {account_no, amount}
    - withdraw: payload {account_no, amount}
    """

    action_map = {
        "get_account": ("GET", "account/{account_no}", None),
        "transfer": ("POST", "account/transfer", "json"),
        "topup": ("PATCH", "account/{account_no}/topup", "json"),
        "withdraw": ("PATCH", "account/{account_no}/withdraw", "json"),
    }

    action = action.lower().strip()
    if action not in action_map:
        logger.error(f"Unsupported action: {action}")
        return {"error": f"Unsupported action '{action}'"}

    method, path_template, body_kind = action_map[action]
    logger.info(f"Processing action: {action}, method: {method}, path_template: {path_template}")

    try:
        path = path_template.format(**payload) if "{" in path_template else path_template
    except KeyError as exc:
        logger.error(f"Missing field in payload: {exc!s}")
        return {"error": f"Missing field: {exc!s}"}

    url = f"{BANK_API}/{path}"
    logger.info(f"Calling URL: {url} with method: {method}")

    try:
        kwargs: dict[str, Any] = {"timeout": 10.0}
        if body_kind == "json":
            kwargs["json"] = payload
            logger.info(f"Request payload: {payload}")

        with httpx.Client() as client:
            response = client.request(method, url, **kwargs)

        logger.info(f"Response status: {response.status_code}")
        
        if response.status_code >= 400:
            logger.error(f"API error: {response.text}")
            return {"error": response.text, "status": response.status_code}

        result = response.json()
        logger.info(f"Response data: {result}")
        return {"success": True, "data": result}

    except Exception as exc:
        logger.exception(f"bank_action failed for action {action}")
        return {"error": str(exc)}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


# Mount MCP with SSE support for ADK connection
app.mount("/mcp", mcp.sse_app())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
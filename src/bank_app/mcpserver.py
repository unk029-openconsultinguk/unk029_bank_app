"""Minimal MCP Server wrapping FastAPI banking endpoints into a single tool."""

import json
import logging
import os
from typing import Any

from fastmcp import FastMCP
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("Bank MCP", host="0.0.0.0", port=8002)

BANK_API = os.getenv("BANK_API_URL", "http://unk029_bank_app:8001")


def _norm_sort_code(code: str | None) -> str | None:
    if not code:
        return None
    digits = "".join(ch for ch in str(code) if ch.isdigit())
    return digits  # if len(digits) == 6 else digits


def _fetch_banks() -> list[dict[str, Any]]:
    try:
        with httpx.Client(timeout=10.0) as client:
            res = client.get(f"{BANK_API}/banks")
        if res.status_code != 200:
            raise RuntimeError(f"Failed to load banks: {res.status_code}")
        banks: list[dict[str, Any]] = res.json()
        return banks
    except Exception as exc:
        logger.error(f"Could not fetch banks from API: {exc}")
        return []


def _build_sortcode_index(banks: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    idx: dict[str, dict[str, Any]] = {}
    for b in banks:
        sc = _norm_sort_code(b.get("sort_code"))
        if sc:
            idx[sc] = b
    return idx


@mcp.tool()
def transfer_money(
    from_account_no: str,
    from_sort_code: str,
    to_account_no: str,
    to_sort_code: str | None = None,
    to_name: str = "Recipient",
    amount: float = 0.0,
    logged_in_account_no: str | None = None,
) -> str | dict[str, Any]:
    """
    Transfer money between accounts using sort codes.
    - For INTERNAL transfers (same bank UNK→UNK): to_sort_code is optional or "11-11-11"
    - For EXTERNAL transfers (different bank): to_sort_code is required (e.g., "60-00-01")

    Args:
        from_account_no: Source UNK Bank account number (the sender)
        from_sort_code: Must be "11-11-11" (UNK Bank sort code)
        to_account_no: Destination account number (where money goes)
        to_sort_code: Optional. Destination bank sort code.
        to_name: Name of the recipient
        amount: Amount to transfer
        logged_in_account_no: The currently logged-in account (for security validation)

    Returns:
        Transfer result with success status and message
    """
    logger.info(
        f"Transfer request: {from_account_no}@{from_sort_code} → "
        f"{to_account_no}@{to_sort_code}, amount={amount}"
    )

    # Common headers for API calls
    headers = {"X-Logged-In-Account": logged_in_account_no or from_account_no}

    try:
        url = f"{BANK_API}/account/transfer"
        payload = {
            "from_account_no": int(from_account_no),
            "to_account_no": int(to_account_no),
            "amount": float(amount),
            "to_sort_code": to_sort_code,
            "to_name": to_name,
        }

        with httpx.Client(timeout=40.0) as client:
            response = client.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            # Try to get a friendly message from the response if it's a string
            try:
                res_data = response.json()
                if isinstance(res_data, str):
                    return res_data
                return f"Successfully transferred £{amount:.2f} to account {to_account_no}."
            except:
                return f"Successfully transferred £{amount:.2f} to account {to_account_no}."
        else:
            error_text = response.text
            try:
                error_json = response.json()
                error_text = error_json.get("detail", error_text)
            except:
                pass
            
            # If it's a sort code error, provide the list of banks
            if "Unknown sort code" in error_text:
                banks = _fetch_banks()
                bank_list_str = "\n".join([
                    f"- {b['name']}: {b['sort_code']}" 
                    for b in banks if not b.get("isInternal")
                ])
                return (
                    f"{error_text}\n\nSupported partner banks are:\n"
                    f"{bank_list_str}\n"
                    "Or use '11-11-11' for internal UNK Bank transfers."
                )
                
            return f"Transfer failed: {error_text}"

    except Exception as exc:
        logger.error(f"Transfer error: {exc}")
        return f"An error occurred during the transfer: {exc!s}"


if __name__ == "__main__":
    mcp.run(transport="sse")

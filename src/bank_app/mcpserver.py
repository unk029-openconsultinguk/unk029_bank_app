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
    to_name: str = "External Account",
    amount: float = 0.0,
    logged_in_account_no: str | None = None,
) -> str | dict[str, Any]:
    """
    Transfer money between accounts using sort codes.
    - For INTERNAL transfers (same bank UNK→UNK): to_sort_code is optional (not needed)
    - For EXTERNAL transfers (different bank): to_sort_code is required

    Args:
        from_account_no: Source UNK Bank account number (the sender)
        from_sort_code: Must be "11-11-11" (UNK Bank sort code)
        to_account_no: Destination account number (where money goes)
        to_sort_code: Optional. Destination bank sort code - "11-11-11" for UNK
            internal, "60-00-01" for Purple Bank, "20-40-41" for Bartley Bank.
            If omitted, defaults to internal UNK transfer.
        to_name: Name of the recipient (required for external transfers)
        amount: Amount to transfer
        logged_in_account_no: The currently logged-in account (for security validation)

    Returns:
        Transfer result with success status and message
    """
    # Load partner banks to get internal sort code
    banks = _fetch_banks()
    sc_index = _build_sortcode_index(banks)
    internal_bank = next((b for b in banks if b.get("isInternal")), None)
    internal_sc = _norm_sort_code(internal_bank.get("sort_code") if internal_bank else None)

    # If to_sort_code not provided, default to internal UNK bank
    if to_sort_code is None:
        to_sort_code = internal_bank.get("sort_code", "11-11-11") if internal_bank else "11-11-11"

    logger.info(
        f"Transfer request: {from_account_no}@{from_sort_code} → "
        f"{to_account_no}@{to_sort_code}, amount={amount}, "
        f"logged_in={logged_in_account_no}"
    )

    # SECURITY: Validate that sender is the logged-in user
    if logged_in_account_no and from_account_no != logged_in_account_no:
        return {
            "success": False,
            "error": (
                f"You can only transfer from your own account "
                f"({logged_in_account_no}). Cannot transfer from "
                f"account {from_account_no}."
            ),
        }

    # Validate source bank is our internal bank
    if _norm_sort_code(from_sort_code) != internal_sc:
        bank_name = internal_bank.get("name", "UNK Bank") if internal_bank else "UNK Bank"
        bank_sortcode = internal_bank.get("sort_code", "11-11-11") if internal_bank else "11-11-11"
        return f"Can only transfer from {bank_name} accounts ({bank_sortcode})"

    # Check if destination bank exists
    norm_to_sc = _norm_sort_code(to_sort_code)
    
    # Build a friendly list of banks for error messages
    bank_list_str = "\n".join([
        f"- {b['name']}: {b['sort_code']}" 
        for b in banks if not b.get("isInternal")
    ])
    
    if not norm_to_sc:
        return (
            "Please provide a destination sort code. For example:\n"
            f"{bank_list_str}\n"
            "Or use '11-11-11' for internal UNK Bank transfers."
        )

    dest_bank = sc_index.get(norm_to_sc)
    if not dest_bank:
        return (
            f"I don't recognize the sort code '{to_sort_code}'. "
            "Supported partner banks are:\n"
            f"{bank_list_str}"
        )

    # Common headers for API calls
    headers = {"X-Logged-In-Account": logged_in_account_no or from_account_no}

    # INTERNAL TRANSFER (same bank)
    if norm_to_sc == internal_sc:
        try:
            url = f"{BANK_API}/account/transfer"
            payload = {
                "from_account_no": int(from_account_no),
                "to_account_no": int(to_account_no),
                "amount": float(amount),
            }

            with httpx.Client(timeout=10.0) as client:
                response = client.post(url, json=payload, headers=headers)

            if response.status_code == 200:
                bank_name = internal_bank.get("name", "UNK Bank") if internal_bank else "UNK Bank"
                return (
                    f"Successfully transferred £{amount:.2f} from account "
                    f"{from_account_no} to account {to_account_no} at "
                    f"{bank_name}. The money has been sent."
                )
            else:
                error_text = response.text
                try:
                    error_json = response.json()
                    error_text = error_json.get("detail", error_text)
                except Exception:
                    pass
                
                # If internal transfer fails because account not found, it might be an external bank
                if "not found" in error_text.lower():
                    return (
                        f"please provide the destination bank sort code, for example:\n"
                        f"{bank_list_str}"
                    )
                return f"Transfer failed: {error_text}"

        except Exception as exc:
            logger.error(f"Internal transfer error: {exc}")
            return f"An error occurred during the transfer: {exc!s}"

    # EXTERNAL TRANSFER (different bank)
    else:
        logger.info(f"External transfer to {dest_bank['name']} via API")
        try:
            url = f"{BANK_API}/account/cross-bank-transfer"
            payload = {
                "from_account_no": int(from_account_no),
                "to_bank_code": dest_bank["code"],
                "to_account_no": int(to_account_no),
                "to_sort_code": to_sort_code,
                "to_name": to_name,
                "amount": float(amount),
            }

            with httpx.Client(timeout=35.0) as client:
                response = client.post(url, json=payload, headers=headers)

            if response.status_code == 200:
                return (
                    f"Successfully transferred £{amount:.2f} from account "
                    f"{from_account_no} at UNK Bank to account {to_account_no} "
                    f"at {dest_bank['name']}. The money has been sent."
                )
            else:
                error_detail = response.text
                try:
                    error_detail = response.json().get("detail", error_detail)
                except Exception:
                    pass
                return f"Transfer to {dest_bank['name']} failed: {error_detail}"

        except Exception as exc:
            logger.error(f"External transfer error: {exc}")
            return f"Could not complete the transfer to {dest_bank['name']}: {exc!s}"


if __name__ == "__main__":
    mcp.run(transport="sse")

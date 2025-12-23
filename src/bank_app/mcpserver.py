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
        amount: Amount to transfer
        logged_in_account_no: The currently logged-in account (for security validation)

    Returns:
        Transfer result with success status and message
    """
    # Load partner banks to get internal sort code
    banks = _fetch_banks()
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

    # Load partner banks dynamically from API (no hard-coded mapping)
    banks = _fetch_banks()
    sc_index = _build_sortcode_index(banks)
    internal_bank = next((b for b in banks if b.get("isInternal")), None)
    internal_sc = _norm_sort_code(internal_bank.get("sort_code") if internal_bank else None)

    # Validate source bank is our internal bank
    if _norm_sort_code(from_sort_code) != internal_sc:
        bank_name = internal_bank.get("name", "UNK Bank") if internal_bank else "UNK Bank"
        bank_sortcode = internal_bank.get("sort_code", "11-11-11") if internal_bank else "11-11-11"
        return f"Can only transfer from {bank_name} accounts ({bank_sortcode})"

    # Check source account exists
    try:
        with httpx.Client(timeout=10.0) as client:
            source_check = client.get(f"{BANK_API}/account/{from_account_no}")
        if source_check.status_code != 200:
            return f"Source account {from_account_no} not found in UNK Bank"
    except Exception as exc:
        return f"Error checking source account: {exc!s}"

    # Check if destination bank exists (normalize input like 600001 or 60-00-01)
    norm_to_sc = _norm_sort_code(to_sort_code)
    if not norm_to_sc:
        return "Missing or invalid destination sort code"
    dest_bank = sc_index.get(norm_to_sc)
    if not dest_bank:
        return f"Unknown destination sort code: {to_sort_code}"

    # INTERNAL TRANSFER (same bank)
    if _norm_sort_code(to_sort_code) == internal_sc:
        bank_name = internal_bank.get("name", "UNK Bank") if internal_bank else "UNK Bank"
        logger.info(f"Internal transfer within {bank_name}")
        try:
            url = f"{BANK_API}/account/transfer"
            payload = {
                "from_account_no": from_account_no,
                "to_account_no": to_account_no,
                "amount": amount,
            }
            # Include the logged-in account as header for backend validation
            headers = {"X-Logged-In-Account": logged_in_account_no or from_account_no}

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
                # Extract detail from JSON if present
                try:
                    error_json = json.loads(error_text)
                    if "detail" in error_json:
                        error_text = error_json["detail"]
                except Exception:
                    pass
                # Check for "not found" to prompt for sort code
                if "not found" in error_text.lower():
                    return (
                        "Please provide the destination bank sort code "
                        "(e.g., 60-00-01 for Purple Bank, 20-40-41 for Bartley Bank)."
                    )
                return error_text

        except Exception as exc:
            logger.error(f"Internal transfer error: {exc}")
            return str(exc)

    # EXTERNAL TRANSFER (different bank)
    else:
        logger.info(f"External transfer to {dest_bank['name']}")

        # Step 1: Withdraw from UNK Bank
        try:
            withdraw_url = f"{BANK_API}/account/{from_account_no}/withdraw"
            withdraw_payload = {"amount": amount}
            headers = {"X-Logged-In-Account": logged_in_account_no or from_account_no}

            with httpx.Client(timeout=10.0) as client:
                withdraw_response = client.patch(
                    withdraw_url, json=withdraw_payload, headers=headers
                )

            if withdraw_response.status_code != 200:
                return f"Failed to withdraw from UNK Bank: {withdraw_response.text}"

            logger.info(f"Withdrew {amount} from account {from_account_no}")

        except Exception as exc:
            logger.error(f"Withdrawal error: {exc}")
            return f"Withdrawal failed: {exc!s}"

        # Step 2: Deposit to external bank
        try:
            # Normalize base URL and build endpoint safely
            base_url = str(dest_bank["url"]).rstrip("/")

            method = dest_bank.get("transferMethod") or dest_bank.get("method")

            if method == "query_params":
                # Deposit via query params at {base_api}/deposit/
                url = f"{base_url}/deposit/"
                params: dict[str, str] = {
                    "account_number": str(to_account_no),
                    "amount": str(amount),
                }

                with httpx.Client(timeout=30.0, verify=False, follow_redirects=True) as client:
                    response = client.post(url, params=params)

            elif method == "deposit":
                # Deposit via JSON at {base_api}/deposit
                url = f"{base_url}/deposit"
                payload = {
                    "account_id": int(to_account_no),
                    "amount": float(amount),
                    "description": f"Transfer from UNK Bank account {from_account_no}",
                }

                with httpx.Client(timeout=30.0, verify=False, follow_redirects=True) as client:
                    response = client.post(url, json=payload)
            else:
                # Rollback: refund to source account
                rollback_url = f"{BANK_API}/account/{from_account_no}/deposit"
                headers = {"X-Logged-In-Account": logged_in_account_no or from_account_no}
                with httpx.Client(timeout=10.0) as client:
                    client.patch(rollback_url, json={"amount": amount}, headers=headers)
                return f"Unknown transfer method for {dest_bank['name']}"

            # Accept any 2xx as success; otherwise, rollback
            if 200 <= response.status_code < 300:
                return (
                    f"Successfully transferred £{amount:.2f} from account "
                    f"{from_account_no} at UNK Bank to account {to_account_no} "
                    f"at {dest_bank['name']}. The money has been sent."
                )
            else:
                # Rollback: refund to source account
                logger.error(f"External deposit failed, rolling back: {response.text}")
                rollback_url = f"{BANK_API}/account/{from_account_no}/deposit"
                with httpx.Client(timeout=10.0) as client:
                    client.patch(rollback_url, json={"amount": amount})

                return (
                    f"External deposit to {dest_bank['name']} failed: "
                    f"{response.text}. Your money has been refunded."
                )

        except Exception as exc:
            logger.error(f"External transfer error: {exc}")
            error_msg = str(exc)
            # Clean up error message
            if "[Errno" in error_msg:
                error_msg = error_msg[error_msg.find("]") + 1 :].strip()
            if "No route to host" in error_msg or "Couldn't connect" in error_msg:
                return f"Unable to connect to {dest_bank['name']}. Please try again later."
            return f"Transfer to {dest_bank['name']} failed: {error_msg}"


if __name__ == "__main__":
    mcp.run(transport="sse")

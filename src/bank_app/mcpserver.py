"""Minimal MCP Server wrapping FastAPI banking endpoints into a single tool."""

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
    return digits if len(digits) == 6 else digits


def _fetch_banks() -> list[dict[str, Any]]:
    try:
        with httpx.Client(timeout=10.0) as client:
            res = client.get(f"{BANK_API}/banks")
        if res.status_code != 200:
            raise RuntimeError(f"Failed to load banks: {res.status_code}")
        return res.json()
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
    to_sort_code: str,
    amount: float
) -> dict[str, Any]:
    """
    Transfer money between accounts using sort codes.
    Automatically handles both internal (same bank) and external (different bank) transfers.
    
    Args:
        from_account_no: Source UNK Bank account number (the sender)
        from_sort_code: Must be "77-91-21" (UNK Bank sort code)
        to_account_no: Destination account number (where money goes)
        to_sort_code: Destination bank sort code - use "77-91-21" for UNK, "60-00-01" for URR034, "20-40-41" for UBF041
        amount: Amount to transfer
    
    Returns:
        Transfer result with success status and message
    """
    logger.info(f"Transfer request: {from_account_no}@{from_sort_code} → {to_account_no}@{to_sort_code}, amount={amount}")

    # Load partner banks dynamically from API (no hard-coded mapping)
    banks = _fetch_banks()
    sc_index = _build_sortcode_index(banks)
    internal_bank = next((b for b in banks if b.get("isInternal")), None)
    internal_sc = _norm_sort_code(internal_bank.get("sort_code") if internal_bank else None)
    
    # Validate source bank is our internal bank
    if _norm_sort_code(from_sort_code) != internal_sc:
        return {"success": False, "error": f"Can only transfer from {internal_bank.get('name','UNK Bank')} accounts ({internal_bank.get('sort_code','77-91-21')})"}
    
    # Check source account exists
    try:
        with httpx.Client(timeout=10.0) as client:
            source_check = client.get(f"{BANK_API}/account/{from_account_no}")
        if source_check.status_code != 200:
            return {"success": False, "error": f"Source account {from_account_no} not found in UNK Bank"}
    except Exception as exc:
        return {"success": False, "error": f"Error checking source account: {str(exc)}"}
    
    # Check if destination bank exists (normalize input like 600001 or 60-00-01)
    norm_to_sc = _norm_sort_code(to_sort_code)
    if not norm_to_sc:
        return {"success": False, "error": "Missing or invalid destination sort code"}
    dest_bank = sc_index.get(norm_to_sc)
    if not dest_bank:
        return {"success": False, "error": f"Unknown destination sort code: {to_sort_code}"}
    
    # INTERNAL TRANSFER (same bank)
    if _norm_sort_code(to_sort_code) == internal_sc:
        logger.info(f"Internal transfer within {internal_bank.get('name','UNK Bank')}")
        try:
            url = f"{BANK_API}/account/transfer"
            payload = {
                "from_account_no": from_account_no,
                "to_account_no": to_account_no,
                "amount": amount
            }
            
            with httpx.Client(timeout=10.0) as client:
                response = client.post(url, json=payload)
            
            if response.status_code == 200:
                return {"success": True, "message": f"✅ Successfully transferred £{amount:.2f} from account {from_account_no} to account {to_account_no} at {internal_bank.get('name','UNK Bank')}!", "data": response.json()}
            else:
                return {"success": False, "error": response.text, "status_code": response.status_code}
                
        except Exception as exc:
            logger.error(f"Internal transfer error: {exc}")
            return {"success": False, "error": str(exc)}
    
    # EXTERNAL TRANSFER (different bank)
    else:
        logger.info(f"External transfer to {dest_bank['name']}")
        
        # Step 1: Withdraw from UNK Bank
        try:
            withdraw_url = f"{BANK_API}/account/{from_account_no}/withdraw"
            withdraw_payload = {"amount": amount}
            
            with httpx.Client(timeout=10.0) as client:
                withdraw_response = client.patch(withdraw_url, json=withdraw_payload)
            
            if withdraw_response.status_code != 200:
                return {
                    "success": False,
                    "error": f"Failed to withdraw from UNK Bank: {withdraw_response.text}",
                    "status_code": withdraw_response.status_code
                }
            
            logger.info(f"Withdrew {amount} from account {from_account_no}")
            
        except Exception as exc:
            logger.error(f"Withdrawal error: {exc}")
            return {"success": False, "error": f"Withdrawal failed: {str(exc)}"}
        
        # Step 2: Deposit to external bank
        try:
            # Normalize base URL and build endpoint safely
            base_url = str(dest_bank["url"]).rstrip("/")

            method = dest_bank.get("transferMethod") or dest_bank.get("method")

            if method == "query_params":
                # Deposit via query params at {base_api}/deposit/
                url = f"{base_url}/deposit/"
                params = {
                    "account_number": str(to_account_no),
                    "amount": float(amount),
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
                rollback_url = f"{BANK_API}/account/{from_account_no}/topup"
                with httpx.Client(timeout=10.0) as client:
                    client.patch(rollback_url, json={"amount": amount})
                return {"success": False, "error": f"Unknown transfer method for {dest_bank['name']}"}

            # Accept any 2xx as success; otherwise, rollback
            if 200 <= response.status_code < 300:
                content_type = response.headers.get("content-type", "").lower()
                try:
                    response_data = response.json() if "application/json" in content_type else {"text": response.text[:500]}
                except Exception:
                    response_data = {"text": response.text[:500]}

                return {
                    "success": True,
                    "message": f"✅ Successfully transferred £{amount:.2f} from account {from_account_no} at UNK Bank to account {to_account_no} at {dest_bank['name']}! The money has been sent.",
                    "data": response_data,
                    "withdrawn_from": from_account_no,
                    "deposit_url": url,
                    "status_code": response.status_code,
                }
            else:
                # Rollback: refund to source account
                logger.error(f"External deposit failed, rolling back: {response.text}")
                rollback_url = f"{BANK_API}/account/{from_account_no}/topup"
                with httpx.Client(timeout=10.0) as client:
                    client.patch(rollback_url, json={"amount": amount})
                
                return {
                    "success": False,
                    "error": f"External deposit failed: {response.text}",
                    "status_code": response.status_code,
                    "bank": dest_bank['name'],
                    "rollback": "completed"
                }
                
        except Exception as exc:
            logger.error(f"External transfer error: {exc}")
            return {"success": False, "error": str(exc), "bank": dest_bank['name']}


if __name__ == "__main__":
    mcp.run(transport="sse")

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

# Other banks we can transfer to (URLs from environment)
URR034_BANK_URL = os.getenv("URR034_BANK_URL", "")
UBF041_BANK_URL = os.getenv("UBF041_BANK_URL", "")

# Sort code to bank mapping
SORT_CODE_MAP = {
    "29-00-01": {"name": "UNK", "url": BANK_API, "type": "internal"},
    "60-00-01": {"name": "URR034", "url": URR034_BANK_URL, "method": "query_params", "type": "external"},
    "20-40-41": {"name": "UBF041", "url": UBF041_BANK_URL, "method": "deposit", "type": "external"},
}


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
        from_account_no: Source account number
        from_sort_code: Source bank sort code (e.g., "29-00-01" for UNK Bank)
        to_account_no: Destination account number
        to_sort_code: Destination bank sort code (e.g., "60-00-01" for URR034, "20-40-41" for UBF041)
        amount: Amount to transfer
    
    Returns:
        Transfer result with success status and message
    """
    logger.info(f"Transfer request: {from_account_no}@{from_sort_code} → {to_account_no}@{to_sort_code}, amount={amount}")
    
    # Validate source bank is UNK
    if from_sort_code not in SORT_CODE_MAP:
        return {"success": False, "error": f"Unknown source sort code: {from_sort_code}"}
    
    if SORT_CODE_MAP[from_sort_code]["type"] != "internal":
        return {"success": False, "error": "Can only transfer from UNK Bank accounts (29-00-01)"}
    
    # Check if destination bank exists
    if to_sort_code not in SORT_CODE_MAP:
        return {"success": False, "error": f"Unknown destination sort code: {to_sort_code}"}
    
    dest_bank = SORT_CODE_MAP[to_sort_code]
    
    # INTERNAL TRANSFER (same bank)
    if to_sort_code == from_sort_code:
        logger.info(f"Internal transfer within UNK Bank")
        try:
            url = f"{BANK_API}/transfer"
            payload = {
                "from_account_no": from_account_no,
                "to_account_no": to_account_no,
                "amount": amount
            }
            
            with httpx.Client(timeout=10.0) as client:
                response = client.post(url, json=payload)
            
            if response.status_code == 200:
                return {"success": True, "message": "Internal transfer completed", "data": response.json()}
            else:
                return {"success": False, "error": response.text, "status_code": response.status_code}
                
        except Exception as exc:
            logger.error(f"Internal transfer error: {exc}")
            return {"success": False, "error": str(exc)}
    
    # EXTERNAL TRANSFER (different bank)
    else:
        logger.info(f"External transfer to {dest_bank['name']}")
        try:
            if dest_bank["method"] == "query_params":
                # URR034 Bank uses query parameters
                url = f"{dest_bank['url']}/api/transfer"
                params = {
                    "from_account_id": from_account_no,
                    "to_account_id": to_account_no,
                    "amount": amount
                }
                
                with httpx.Client(timeout=10.0, verify=False) as client:
                    response = client.get(url, params=params)
                    
            elif dest_bank["method"] == "deposit":
                # UBF041 Bank uses POST with JSON body
                url = f"{dest_bank['url']}/api/deposit"
                payload = {
                    "from_account_id": from_account_no,
                    "to_account_id": to_account_no,
                    "amount": amount
                }
                
                with httpx.Client(timeout=10.0, verify=False) as client:
                    response = client.post(url, json=payload)
            else:
                return {"success": False, "error": f"Unknown transfer method for {dest_bank['name']}"}
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": f"External transfer to {dest_bank['name']} completed",
                    "data": response.json()
                }
            else:
                return {
                    "success": False,
                    "error": response.text,
                    "status_code": response.status_code,
                    "bank": dest_bank['name']
                }
                
        except Exception as exc:
            logger.error(f"External transfer error: {exc}")
            return {"success": False, "error": str(exc), "bank": dest_bank['name']}


# ============ COMMENTED OUT OLD TOOLS ============
"""
@mcp.tool()
def check_account_exists(account_no: str) -> dict[str, Any]:
    """Check if an account exists in UNK bank."""
    url = f"{BANK_API}/account/{account_no}"
    logger.info(f"Checking account: {account_no}")
    
    try:
        with httpx.Client() as client:
            response = client.get(url, timeout=10.0)
            
        if response.status_code == 200:
            return {"exists": True, "account_data": response.json(), "bank": "UNK"}
        else:
            return {"exists": False}
            
    except Exception as exc:
        logger.error(f"Error checking account {account_no}: {exc}")
        return {"exists": False, "error": str(exc)}


@mcp.tool()
def get_available_banks() -> dict[str, Any]:
    """Fetch available external banks and their sort codes."""
    banks_info = {}
    
    bank_apis = {
        "URR034": {"url": URR034_BANK_URL, "method": "query_params", "sort_code": "60-00-01"},
        "UBF041": {"url": UBF041_BANK_URL, "method": "deposit", "sort_code": "20-40-41"}
    }
    
    for bank_name, config in bank_apis.items():
        if not config["url"]:
            continue
            
        try:
            with httpx.Client(timeout=10.0, verify=False) as client:
                response = client.get(f"{config['url']}/api")
                
            if response.status_code == 200:
                bank_data = response.json()
                banks_info[bank_name] = {
                    "name": bank_data.get("bank_name", bank_name),
                    "sort_code": bank_data.get("sort_code", config["sort_code"]),
                    "url": config["url"],
                    "status": "online"
                }
            else:
                banks_info[bank_name] = {
                    "name": f"{bank_name} Bank",
                    "sort_code": config["sort_code"],
                    "url": config["url"],
                    "status": "offline"
                }
        except Exception as exc:
            logger.error(f"Error fetching {bank_name}: {exc}")
            banks_info[bank_name] = {
                "name": f"{bank_name} Bank",
                "sort_code": config["sort_code"],
                "url": config["url"],
                "status": "error",
                "error": str(exc)
            }
    
    return {"banks": banks_info, "total": len(banks_info)}


@mcp.tool()
def unk_bank(action: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Perform banking actions via the FastAPI backend.

    Actions:
    - get_account: payload must contain 'account_no'
    - transfer: payload must contain 'from_account_no', 'to_account_no', 'amount'
    - topup: payload must contain 'account_no', 'amount'
    - withdraw: payload must contain 'account_no', 'amount'
    
    Example: unk_bank(action='transfer', payload={'from_account_no': '11111111', 'to_account_no': '22222222', 'amount': 100})
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
        return {"error": f"Unsupported action '{action}'. Available: get_account, transfer, topup, withdraw"}

    method, path_template, body_kind = action_map[action]
    logger.info(f"Processing action: {action}, method: {method}, path_template: {path_template}, payload: {payload}")

    # Build the path from template
    try:
        if "{" in path_template:
            path = path_template.format(**payload)
        else:
            path = path_template
    except KeyError as exc:
        logger.error(f"Missing field in payload: {exc!s}")
        return {"error": f"Missing required field in payload: {exc!s}. Payload received: {payload}"}

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


@mcp.tool()
def cross_bank_transfer(
    from_account_no: str, to_bank: str, to_account_no: str, amount: float
) -> dict[str, Any]:
    """Transfer money from UNK bank to another bank.

    Args:
        from_account_no: Your UNK bank account number (source)
        to_bank: The destination bank code OR sort code (e.g., 'urr034', '60-00-01', 'ubf041', '20-40-41')
        to_account_no: The destination account number at the other bank
        amount: Amount to transfer

    Available: urr034 (60-00-01), ubf041 (20-40-41)
    """
    logger.info(
        f"Cross-bank transfer: {from_account_no} -> {to_bank}:{to_account_no}, amount: {amount}"
    )

    # Map sort codes to bank codes
    sort_code_map = {
        "60-00-01": "urr034",
        "600001": "urr034",
        "20-40-41": "ubf041",
        "204041": "ubf041"
    }
    
    to_bank = to_bank.lower().strip().replace(" ", "")
    if to_bank in sort_code_map:
        to_bank = sort_code_map[to_bank]
        logger.info(f"Mapped sort code to bank: {to_bank}")
    
    if to_bank not in OTHER_BANKS:
        return {"error": f"Unknown bank '{to_bank}'. Available: {list(OTHER_BANKS.keys())}"}

    if amount <= 0:
        return {"error": "Amount must be positive"}

    bank_config = OTHER_BANKS[to_bank]

    try:
        with httpx.Client(timeout=15.0, verify=False) as client:
            # Step 1: Withdraw from UNK bank account
            withdraw_url = f"{BANK_API}/account/{from_account_no}/withdraw"
            withdraw_resp = client.patch(withdraw_url, json={"amount": amount})

            if withdraw_resp.status_code >= 400:
                return {"error": f"Withdraw failed: {withdraw_resp.text}"}

            withdraw_data = withdraw_resp.json()
            logger.info(f"Withdraw successful: {withdraw_data}")

            # Step 2: Transfer to other bank (different APIs)
            other_bank_url = bank_config["url"]
            transfer_resp = None

            if bank_config["method"] == "query_params":
                # URR034 style: POST /transfer/?from_account_id=X&to_account_id=Y&amount=Z
                transfer_url = f"{other_bank_url}/transfer/"
                params = {
                    "from_account_id": "EXTERNAL_UNK",
                    "to_account_id": to_account_no,
                    "amount": str(amount),
                }
                transfer_resp = client.post(transfer_url, params=params)

            elif bank_config["method"] == "deposit":
                # UBF041 style: POST /api/deposit with JSON body
                transfer_url = f"{other_bank_url}/api/deposit"
                json_body = {
                    "account_id": int(to_account_no),
                    "amount": amount,
                    "description": f"Transfer from UNK account {from_account_no}",
                }
                transfer_resp = client.post(transfer_url, json=json_body)

            if transfer_resp is None or transfer_resp.status_code >= 400:
                # Rollback: topup the withdrawn amount back
                error_text = transfer_resp.text if transfer_resp else "No response"
                logger.error(f"External transfer failed, rolling back: {error_text}")
                rollback_url = f"{BANK_API}/account/{from_account_no}/topup"
                client.patch(rollback_url, json={"amount": amount})
                return {"error": f"Transfer to {to_bank} failed: {error_text}"}

            transfer_data = transfer_resp.json()
            logger.info(f"Cross-bank transfer successful: {transfer_data}")

            return {
                "success": True,
                "message": (
                    f"Transferred {amount} from UNK account {from_account_no} "
                    f"to {to_bank} account {to_account_no}"
                ),
                "from_balance": withdraw_data.get("balance", withdraw_data),
                "external_result": transfer_data,
            }

    except Exception as exc:
        logger.exception("Cross-bank transfer failed")
        return {"error": str(exc)}


# Run the MCP server when executed
if __name__ == "__main__":
    mcp.run(transport="sse")
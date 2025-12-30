import requests
import logging
import os
import json
from typing import Any

logger = logging.getLogger(__name__)

def get_internal_bank() -> dict[str, Any]:
    """Fetch internal bank details from environment."""
    try:
        return json.loads(os.getenv("INTERNAL_BANK", '{"code": "unk029", "name": "UNK Bank (Internal)", "url": "/api", "isInternal": true, "transferMethod": "internal", "sort_code": "11-11-11"}'))
    except Exception as e:
        logger.error(f"Error parsing INTERNAL_BANK: {e}")
        return {"code": "unk029", "name": "UNK Bank (Internal)", "url": "/api", "isInternal": True, "transferMethod": "internal", "sort_code": "11-11-11"}

def get_external_banks() -> list[dict[str, Any]]:
    """Fetch external bank details from environment."""
    try:
        return json.loads(os.getenv("EXTERNAL_BANKS", "[]"))
    except Exception as e:
        logger.error(f"Error parsing EXTERNAL_BANKS: {e}")
        return []

# For backward compatibility and easy access
INTERNAL_BANK = get_internal_bank()
EXTERNAL_BANKS = get_external_banks()

def get_partner_bank_mapping() -> dict[str, dict[str, Any]]:
    """Returns a mapping of all banks by their code."""
    banks = [get_internal_bank()] + get_external_banks()
    return {bank["code"]: bank for bank in banks}


def discover_deposit_endpoint(bank_url: str) -> tuple[str, str]:
    """
    Automatically finds the deposit endpoint and method by parsing the bank's OpenAPI schema.

    Args:
        bank_url: The base URL of the partner bank API.

    Returns:
        A tuple of (endpoint_path, http_method).
    """
    try:
        # 1. Try to fetch the OpenAPI schema
        schema_url = f"{bank_url.rstrip('/')}/openapi.json"
        logger.info(f"Attempting to discover endpoint from {schema_url}")

        response = requests.get(schema_url, timeout=5, verify=False)

        if response.status_code == 200:
            schema = response.json()
            paths = schema.get("paths", {})

            # 2. Search for a path that contains 'deposit' and supports POST, PATCH, or PUT
            allowed_methods = ["post", "patch", "put"]
            
            # Priority 1: Exact match /deposit
            for path, methods in paths.items():
                for m in allowed_methods:
                    if m in [k.lower() for k in methods.keys()]:
                        if path.lower().endswith("/deposit") or path.lower().endswith("/deposit/"):
                            logger.info(f"Discovered exact deposit endpoint: {path} [{m}]")
                            return path, m

            # Priority 2: Any path containing 'deposit'
            for path, methods in paths.items():
                for m in allowed_methods:
                    if m in [k.lower() for k in methods.keys()]:
                        if "deposit" in path.lower():
                            logger.info(f"Discovered potential deposit endpoint: {path} [{m}]")
                            return path, m

    except Exception as e:
        logger.error(f"Discovery failed for {bank_url}: {e}")

    # 3. Fallback to a default if discovery fails
    logger.warning(f"Discovery failed for {bank_url}, falling back to /deposit [post]")
    return "/deposit", "post"


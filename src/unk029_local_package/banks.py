from typing import Any

INTERNAL_BANK = {
    "code": "unk029",
    "name": "UNK Bank (Internal)",
    "url": "/api",
    "isInternal": True,
    "transferMethod": "internal",
    "sort_code": "11-11-11",
}

EXTERNAL_BANKS = [
    {
        "code": "urr034",
        "name": "Purple Bank",
        "url": "https://urr034.dev.openconsultinguk.com/api",
        "isInternal": False,
        "transferMethod": "query_params",  # POST /api/deposit/?account_number&amount
        "sort_code": "60-00-01",
    },
    {
        "code": "ubf041",
        "name": "Bartley Bank",
        "url": "https://ubf041.dev.openconsultinguk.com/api",
        "isInternal": False,
        "transferMethod": "deposit",  # POST /api/deposit with JSON body
        "sort_code": "20-40-41",
    },
    {
        "code": "uia037",
        "name": "Secure Bank",
        "url": "https://uia037.dev.openconsultinguk.com/api",
        "isInternal": False,
        "transferMethod": "deposit",
        "sort_code": "11-22-33",
    },
    {
        "code": "uss016",
        "name": "AppyPay",
        "url": "https://uss016.dev.openconsultinguk.com/api",
        "isInternal": False,
        "transferMethod": "deposit",
        "sort_code": "33-44-55",
    },
]

# Mapping list for easy lookup by code
PARTNER_BANK_MAPPING = {bank["code"]: bank for bank in [INTERNAL_BANK] + EXTERNAL_BANKS}

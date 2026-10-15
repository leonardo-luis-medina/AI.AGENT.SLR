import json
from pathlib import Path

# Locate our dataset
DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "deals.json"


def get_deal(deal_id: str) -> dict:
    """Retrieve a solar installation deal using its ID."""

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        deals = json.load(file)

    for deal in deals:
        if deal["deal_id"] == deal_id:
            return deal

    return {
        "error": f"Deal {deal_id} not found"
    }

def check_system_size(deal_id: str) -> dict:
    """R01: Check whether a deal has a valid positive system size."""

    deal = get_deal(deal_id)

    if "error" in deal:
        return deal

    size = deal.get("system_size_kw")

    if not isinstance(size, (int, float)) or isinstance(size, bool) or size <= 0:
        return {
            "rule": "R01",
            "result": "FAIL",
            "reason": "System size must be greater than 0 kW."
        }

    return {
        "rule": "R01",
        "result": "PASS",
        "reason": f"System size of {size} kW is valid."
    }

def check_required_fields(deal_id: str) -> dict:
    """R02: Check whether essential deal information is present."""

    deal = get_deal(deal_id)

    if "error" in deal:
        return deal

    required_fields = [
        "deal_id",
        "customer_name",
        "state",
        "system_size_kw",
        "roof_type"
    ]

    missing_fields = [
        field
        for field in required_fields
        if deal.get(field) is None
        or (isinstance(deal.get(field), str) and not deal.get(field).strip())
    ]

    if missing_fields:
        return {
            "rule": "R02",
            "result": "FAIL",
            "reason": f"Missing required fields: {', '.join(missing_fields)}"
        }

    return {
        "rule": "R02",
        "result": "PASS",
        "reason": "All required deal fields are present."
    }
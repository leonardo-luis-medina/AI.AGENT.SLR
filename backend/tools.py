import json
from pathlib import Path
from backend.deal_context import get_context_deal


# Locate our dataset
DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "deals.json"


def get_deal_from_file(deal_id: str) -> dict:
    """Retrieve a solar installation deal using its ID."""

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        deals = json.load(file)

    for deal in deals:
        if deal["deal_id"] == deal_id:
            return deal

    return {
        "error": f"Deal {deal_id} not found"
    }

def get_deal(deal_id: str) -> dict:
    return get_context_deal(deal_id, get_deal_from_file)


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

def check_state(deal_id: str) -> dict:
    """R03: Validate Australian state or territory codes."""

    deal = get_deal(deal_id)

    if "error" in deal:
        return deal

    valid_states = {
        "NSW", "VIC", "QLD", "WA",
        "SA", "TAS", "ACT", "NT"
    }

    state = deal.get("state")

    if not isinstance(state, str) or state not in valid_states:
        return {
            "rule": "R03",
            "result": "FAIL",
            "reason": f"Invalid Australian state code: {state}"
        }

    return {
        "rule": "R03",
        "result": "PASS",
        "reason": f"Australian state code {state} is valid."
    }

def check_roof_type(deal_id: str) -> dict:
    """R04: Validate the roof type recorded in a solar deal."""

    deal = get_deal(deal_id)

    if "error" in deal:
        return deal

    valid_roof_types = {"tile", "metal", "concrete"}

    roof_type = deal.get("roof_type")

    if not isinstance(roof_type, str) or roof_type not in valid_roof_types:
        return {
            "rule": "R04",
            "result": "FAIL",
            "reason": f"Invalid or missing roof type: {roof_type}"
        }

    return {
        "rule": "R04",
        "result": "PASS",
        "reason": f"Roof type '{roof_type}' is valid."
    }

from datetime import date


def check_cash_deposit(deal_id: str) -> dict:
    """R05: Cash jobs require a deposit of at least 5%."""

    deal = get_deal(deal_id)
    if "error" in deal:
        return deal

    if deal.get("payment_type") != "cash":
        return {
            "rule": "R05",
            "result": "PASS",
            "reason": "Not a cash job; deposit rule does not apply."
        }

    total = deal.get("total_price")
    deposit = deal.get("deposit_amount")

    if (
        not isinstance(total, (int, float))
        or isinstance(total, bool)
        or total <= 0
        or not isinstance(deposit, (int, float))
        or isinstance(deposit, bool)
        or deposit < 0
    ):
        return {
            "rule": "R05",
            "result": "NEEDS_HUMAN",
            "reason": "Missing or invalid price/deposit information."
        }

    if deposit < total * 0.05:
        return {
            "rule": "R05",
            "result": "FAIL",
            "reason": "Cash deposit is below 5%."
        }

    return {
        "rule": "R05",
        "result": "PASS",
        "reason": "Cash deposit meets the 5% requirement."
    }


def check_signature_date(deal_id: str) -> dict:
    """R06: Signature date must be on or before sale date."""

    deal = get_deal(deal_id)
    if "error" in deal:
        return deal

    try:
        signature = date.fromisoformat(deal["signature_date"])
        sale = date.fromisoformat(deal["sale_date"])
    except (KeyError, ValueError, TypeError):
        return {
            "rule": "R06",
            "result": "NEEDS_HUMAN",
            "reason": "Missing or invalid signature/sale date."
        }

    return {
        "rule": "R06",
        "result": "PASS" if signature <= sale else "FAIL",
        "reason": (
            "Signature date is on or before sale date."
            if signature <= sale
            else "Signature date is after sale date."
        )
    }


def check_install_date(deal_id: str) -> dict:
    """R07: Installation must be requested at least 7 days after sale."""

    deal = get_deal(deal_id)
    if "error" in deal:
        return deal

    try:
        sale = date.fromisoformat(deal["sale_date"])
        install = date.fromisoformat(deal["requested_install_date"])
    except (KeyError, ValueError, TypeError):
        return {
            "rule": "R07",
            "result": "NEEDS_HUMAN",
            "reason": "Missing or invalid sale/installation date."
        }

    days = (install - sale).days

    return {
        "rule": "R07",
        "result": "PASS" if days >= 7 else "FAIL",
        "reason": f"Requested installation is {days} days after sale."
    }


def check_sold_documents(deal_id: str) -> dict:
    """R08: Sold deals require switchboard photo and electricity bill."""

    deal = get_deal(deal_id)
    if "error" in deal:
        return deal

    stage = deal.get("stage")

    if not isinstance(stage, str):
        return {
            "rule": "R08",
            "result": "NEEDS_HUMAN",
            "reason": "Deal stage is missing or invalid."
        }

    if stage.strip().lower() != "sold":
        return {
            "rule": "R08",
            "result": "PASS",
            "reason": "Deal is not at Sold stage; document rule does not apply."
        }

    missing = []

    if deal.get("switchboard_photo_received") is not True:
        missing.append("switchboard photo")

    if deal.get("electricity_bill_received") is not True:
        missing.append("electricity bill")

    return {
        "rule": "R08",
        "result": "FAIL" if missing else "PASS",
        "reason": (
            f"Missing required documents: {', '.join(missing)}"
            if missing
            else "Both required documents have been received."
        )
    }


def check_postcode_state(deal_id: str) -> dict:
    """R09: Validate postcode against state using demo postcode ranges."""

    deal = get_deal(deal_id)
    if "error" in deal:
        return deal

    postcode = str(deal.get("postcode", ""))
    state = deal.get("state")

    # Simplified demonstration mapping, not a complete Australian postcode database.
    prefixes = {
        "NSW": "2",
        "VIC": "3",
        "QLD": "4",
        "SA": "5",
        "WA": "6",
        "TAS": "7"
    }

    if not isinstance(state, str) or state not in prefixes:
        return {
            "rule": "R09",
            "result": "NEEDS_HUMAN",
            "reason": "State is missing or unsupported by demo postcode mapping."
        }

    if not (len(postcode) == 4 and postcode.isascii() and postcode.isdigit()):
        return {
            "rule": "R09",
            "result": "NEEDS_HUMAN",
            "reason": "Postcode is missing or invalid."
        }

    valid = postcode.startswith(prefixes[state])

    return {
        "rule": "R09",
        "result": "PASS" if valid else "FAIL",
        "reason": (
            f"Postcode {postcode} matches state {state}."
            if valid
            else f"Postcode {postcode} does not match state {state}."
        )
    }
from datetime import datetime

from backend.agent_orchestrator import execute_agent
from backend.integrations.normalizer import normalize_google_sheet_deal


REQUIRED_FIELDS = [
    "deal_id",
    "customer_name",
    "state",
    "postcode",
    "roof_type",
    "system_size_kw",
    "payment_type",
    "total_price",
    "deposit_amount",
    "sale_date",
    "signature_date",
    "requested_install_date",
    "stage",
    "switchboard_photo_received",
    "electricity_bill_received",
    "notes",
]


def convert_boolean(value):
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        normalized = value.strip().lower()

        if normalized in {"true", "yes", "1"}:
            return True

        if normalized in {"false", "no", "0"}:
            return False

    raise ValueError(f"Invalid boolean value: {value!r}")


def convert_number(value):
    if isinstance(value, bool):
        raise ValueError("Boolean is not a valid number.")

    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Invalid numeric value: {value!r}"
        ) from exc


def validate_date(value):
    if not isinstance(value, str):
        raise ValueError("Date must be a string.")

    try:
        datetime.strptime(value.strip(), "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(
            f"Invalid date: {value!r}. Expected YYYY-MM-DD."
        ) from exc

    return value.strip()


def prepare_google_sheet_deal(raw_record):
    if not isinstance(raw_record, dict):
        raise ValueError(
            "Google Sheets record must be a dictionary."
        )

    missing = [
        field
        for field in REQUIRED_FIELDS
        if field not in raw_record
    ]

    if missing:
        raise ValueError(
            f"Missing spreadsheet columns: {', '.join(missing)}"
        )

    deal = normalize_google_sheet_deal(raw_record)

    deal["deal_id"] = str(deal["deal_id"]).strip()

    if not deal["deal_id"]:
        raise ValueError("Deal ID cannot be empty.")

    for field in [
        "system_size_kw",
        "total_price",
        "deposit_amount",
    ]:
        deal[field] = convert_number(deal[field])

    for field in [
        "switchboard_photo_received",
        "electricity_bill_received",
    ]:
        deal[field] = convert_boolean(deal[field])

    for field in [
        "sale_date",
        "signature_date",
        "requested_install_date",
    ]:
        deal[field] = validate_date(deal[field])

    return deal


def run_external_qc(raw_record, selected_rules=None):
    """
    Run QC using request-specific deal data.

    No global monkeypatching is used, allowing concurrent
    requests to process different deals independently.
    """

    deal = prepare_google_sheet_deal(raw_record)

    return execute_agent(
        deal["deal_id"],
        selected_rules=selected_rules,
        deal_data=deal,
    )
from copy import deepcopy

from backend.integrations.external_qc import run_external_qc


DETERMINISTIC_RULES = [
    f"R{i:02d}" for i in range(1, 10)
]


SAMPLE_DEALS = {
    "Complete Sale": {
        "deal_id": "DEMO-INTERACTIVE-001",
        "customer_name": "Jordan Parker",
        "state": "NSW",
        "postcode": "2000",
        "roof_type": "tile",
        "system_size_kw": 6.6,
        "payment_type": "cash",
        "total_price": 12000,
        "deposit_amount": 1200,
        "sale_date": "2026-10-16",
        "signature_date": "2026-10-16",
        "requested_install_date": "2026-11-10",
        "stage": "Sold",
        "switchboard_photo_received": True,
        "electricity_bill_received": True,
        "notes": "Customer confirmed roof access.",
    },
    "Missing Requirements": {
        "deal_id": "DEMO-INTERACTIVE-002",
        "customer_name": "Taylor Morgan",
        "state": "VIC",
        "postcode": "3000",
        "roof_type": "metal",
        "system_size_kw": 6.6,
        "payment_type": "cash",
        "total_price": 12000,
        "deposit_amount": 100,
        "sale_date": "2026-10-16",
        "signature_date": "2026-10-16",
        "requested_install_date": "2026-11-10",
        "stage": "Sold",
        "switchboard_photo_received": True,
        "electricity_bill_received": False,
        "notes": "Electricity bill is missing.",
    },
    "Roof Requires Review": {
        "deal_id": "DEMO-INTERACTIVE-003",
        "customer_name": "Casey Wilson",
        "state": "QLD",
        "postcode": "4000",
        "roof_type": "unknown",
        "system_size_kw": 6.6,
        "payment_type": "cash",
        "total_price": 12000,
        "deposit_amount": 1200,
        "sale_date": "2026-10-16",
        "signature_date": "2026-10-16",
        "requested_install_date": "2026-11-10",
        "stage": "Sold",
        "switchboard_photo_received": True,
        "electricity_bill_received": True,
        "notes": "Roof requires additional confirmation.",
    },
}


def get_sample_deals():
    """Return independent copies of the fictional sample deals."""
    return deepcopy(SAMPLE_DEALS)


def run_interactive_qc(deal, mode="deterministic"):
    """
    Run SolarQC on a fictional deal.

    deterministic: R01-R09, no Ollama required.
    full_ai: R01-R11, requires configured local AI.
    """

    if mode == "deterministic":
        selected_rules = DETERMINISTIC_RULES

    elif mode == "full_ai":
        selected_rules = None

    else:
        raise ValueError(f"Unsupported QC mode: {mode}")

    result = run_external_qc(
        deepcopy(deal),
        selected_rules=selected_rules,
    )

    if not isinstance(result, dict):
        raise ValueError("Invalid QC engine response.")

    if "error" in result:
        raise ValueError(str(result["error"]))

    return {
        "mode": mode,
        "qc": result,
    }
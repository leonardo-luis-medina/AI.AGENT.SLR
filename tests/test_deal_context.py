from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy

from backend.agent_orchestrator import execute_agent
from backend.deal_context import get_context_deal


BASE_DEAL = {
    "deal_id": "TEST-001",
    "customer_name": "Jordan Parker",
    "state": "NSW",
    "postcode": "2000",
    "system_size_kw": 6.6,
    "roof_type": "tile",
    "payment_type": "cash",
    "deposit_amount": 1200.0,
    "total_price": 12000.0,
    "sale_date": "2026-10-16",
    "signature_date": "2026-10-16",
    "requested_install_date": "2026-11-10",
    "contract_received": True,
    "electricity_bill_received": True,
    "switchboard_photo_received": True,
    "notes": "Customer confirmed roof access.",
    "stage": "Sold",
}


def test_concurrent_deals_are_isolated():
    def process_deal(deal_id, system_size):
        deal = deepcopy(BASE_DEAL)
        deal["deal_id"] = deal_id
        deal["system_size_kw"] = system_size

        return execute_agent(
            deal_id,
            selected_rules=["R01"],
            deal_data=deal,
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_a = executor.submit(process_deal, "TEST-A", 6.6)
        future_b = executor.submit(process_deal, "TEST-B", -1)

        result_a = future_a.result()
        result_b = future_b.result()

    assert result_a["deal_id"] == "TEST-A"
    assert result_a["results"][0]["result"] == "PASS"

    assert result_b["deal_id"] == "TEST-B"
    assert result_b["results"][0]["result"] == "FAIL"


def test_deal_context_is_reset():
    deal = deepcopy(BASE_DEAL)

    result = execute_agent(
        deal["deal_id"],
        selected_rules=["R01"],
        deal_data=deal,
    )

    assert result["overall_status"] == "PASS"

    fallback = lambda deal_id: {"error": "Deal not found"}

    assert get_context_deal("TEST-001", fallback) == {
        "error": "Deal not found"
    }


def test_file_based_qc_still_works():
    import json
    from pathlib import Path

    deals_path = (
        Path(__file__).resolve().parents[1]
        / "data"
        / "deals.json"
    )

    with deals_path.open("r", encoding="utf-8") as file:
        deals = json.load(file)

    if isinstance(deals, list):
        deal_id = deals[0]["deal_id"]
    else:
        deal_id = next(iter(deals))

    result = execute_agent(
        deal_id,
        selected_rules=["R01"],
    )

    assert "error" not in result, result
    assert result["results"][0]["rule"] == "R01"
    assert result["results"][0]["result"] in {
        "PASS",
        "FAIL",
        "NEEDS_HUMAN",
    }
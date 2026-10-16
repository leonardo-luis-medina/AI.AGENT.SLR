from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from threading import Barrier

from backend.agent_orchestrator import execute_agent
from backend.deal_context import use_deal
from backend.tools import get_deal


BASE_DEAL = {
    "deal_id": "STRESS-BASE",
    "customer_name": "Test Customer",
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


def test_overlapping_deal_contexts_are_isolated():
    barrier = Barrier(2)

    def worker(deal_id, system_size):
        deal = deepcopy(BASE_DEAL)
        deal["deal_id"] = deal_id
        deal["system_size_kw"] = system_size

        with use_deal(deal):
            barrier.wait(timeout=10)

            visible_deal = get_deal(deal_id)

            result = execute_agent(
                deal_id,
                selected_rules=["R01"],
            )

            return visible_deal, result

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_a = executor.submit(worker, "STRESS-A", 6.6)
        future_b = executor.submit(worker, "STRESS-B", -1)

        deal_a, result_a = future_a.result()
        deal_b, result_b = future_b.result()

    assert deal_a["deal_id"] == "STRESS-A"
    assert deal_b["deal_id"] == "STRESS-B"

    assert result_a["results"][0]["result"] == "PASS"
    assert result_b["results"][0]["result"] == "FAIL"


def test_context_cleanup_after_exception():
    deal = deepcopy(BASE_DEAL)
    deal["deal_id"] = "STRESS-ERROR"

    try:
        with use_deal(deal):
            assert get_deal("STRESS-ERROR")["deal_id"] == "STRESS-ERROR"
            raise RuntimeError("Simulated processing failure")

    except RuntimeError:
        pass

    assert get_deal("STRESS-ERROR") == {
        "error": "Deal STRESS-ERROR not found"
    }


def test_many_concurrent_deals():
    def worker(index):
        deal = deepcopy(BASE_DEAL)
        deal["deal_id"] = f"STRESS-{index:03d}"
        deal["system_size_kw"] = 6.6 if index % 2 == 0 else -1

        return execute_agent(
            deal["deal_id"],
            selected_rules=["R01"],
            deal_data=deal,
        )

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(worker, range(50)))

    assert len(results) == 50

    for index, result in enumerate(results):
        assert result["deal_id"] == f"STRESS-{index:03d}"

        expected = "PASS" if index % 2 == 0 else "FAIL"

        assert result["results"][0]["result"] == expected
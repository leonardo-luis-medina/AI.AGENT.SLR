from collections import Counter
from backend.tools import (
    check_system_size,
    check_required_fields,
    check_state,
    check_roof_type,
    check_cash_deposit,
    check_signature_date,
    check_install_date,
    check_sold_documents,
    check_postcode_state,
)

CHECKS = [
    check_system_size,
    check_required_fields,
    check_state,
    check_roof_type,
    check_cash_deposit,
    check_signature_date,
    check_install_date,
    check_sold_documents,
    check_postcode_state,
]

EXPECTED_FAILURES = {
    1: "R01",
    2: "R03",
    3: "R04",
    4: "R05",
    5: "R06",
    6: "R07",
    7: "R08",
    8: "R09",
}

counts = Counter()
mismatches = []

for number in range(1, 101):
    deal_id = f"DEAL-{number:03d}"
    results = [check(deal_id) for check in CHECKS]

    actual_failures = {
        result["rule"]
        for result in results
        if result.get("result") == "FAIL"
    }

    expected_rule = EXPECTED_FAILURES.get(number % 10)
    expected_failures = {expected_rule} if expected_rule else set()

    if actual_failures != expected_failures:
        mismatches.append({
            "deal_id": deal_id,
            "expected": sorted(expected_failures),
            "actual": sorted(actual_failures),
        })

    for result in results:
        counts[result.get("result", "UNKNOWN")] += 1

print("Total deterministic checks:", sum(counts.values()))
print("Result counts:", dict(counts))
print("Deals with unexpected FAIL results:", len(mismatches))

for mismatch in mismatches[:10]:
    print(mismatch)
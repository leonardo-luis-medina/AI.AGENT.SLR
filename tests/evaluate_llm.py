from backend.tools import get_deal
from backend.llm_checks import analyze_deal_notes

deal_numbers = [9, 10, 19, 20, 29, 30, 39, 40, 49, 50]

correct = 0

for number in deal_numbers:
    deal_id = f"DEAL-{number:03d}"
    deal = get_deal(deal_id)

    results = analyze_deal_notes(deal)

    expected = "FAIL" if number % 10 == 9 else "PASS"
    actual = results.get("R10", {}).get("result", "NEEDS_HUMAN")

    passed = actual == expected
    correct += passed

    print(
        f"{deal_id}: "
        f"Expected={expected}, "
        f"Actual={actual}, "
        f"{'CORRECT' if passed else 'INCORRECT'}"
    )

print(f"\nR10 accuracy: {correct}/{len(deal_numbers)}")
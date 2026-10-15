from backend.tools import get_deal
from backend.llm_checks import analyze_deal_notes

deal_numbers = [10, 20, 30, 40, 50]

correct = 0

for number in deal_numbers:
    deal_id = f"DEAL-{number:03d}"
    deal = get_deal(deal_id)

    # Create an explicit contradiction for evaluation.
    deal["roof_type"] = "metal"
    deal["notes"] = (
        "Customer confirmed the roof is tile. "
        "Installation access is clear."
    )

    results = analyze_deal_notes(deal)
    actual = results.get("R11", {}).get("result")

    passed = actual == "FAIL"
    correct += passed

    print(
        f"{deal_id}: Expected=FAIL, "
        f"Actual={actual}, "
        f"{'CORRECT' if passed else 'INCORRECT'}"
    )

print(f"\nR11 accuracy: {correct}/{len(deal_numbers)}")
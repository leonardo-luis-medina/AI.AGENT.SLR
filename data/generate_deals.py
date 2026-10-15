import json
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)

OUTPUT = Path(__file__).resolve().parent / "deals.json"

LOCATIONS = [
    ("NSW", "2000"),
    ("VIC", "3000"),
    ("QLD", "4000"),
    ("SA", "5000"),
    ("WA", "6000"),
    ("TAS", "7000"),
]

ROOF_TYPES = ["tile", "metal", "concrete"]


def create_deal(number):
    state, postcode = random.choice(LOCATIONS)
    roof = random.choice(ROOF_TYPES)

    sale_date = date(2026, 9, 1) + timedelta(
        days=random.randint(0, 29)
    )

    payment_type = random.choice(["cash", "finance"])
    total_price = random.randint(5000, 20000)

    deal = {
        "deal_id": f"DEAL-{number:03d}",
        "customer_name": f"Demo Customer {number:03d}",
        "state": state,
        "postcode": postcode,
        "roof_type": roof,
        "system_size_kw": random.choice([5.0, 6.6, 8.0, 10.0]),
        "payment_type": payment_type,
        "total_price": total_price,
        "deposit_amount": round(total_price * 0.10, 2),
        "sale_date": sale_date.isoformat(),
        "signature_date": (
            sale_date - timedelta(days=1)
        ).isoformat(),
        "requested_install_date": (
            sale_date + timedelta(days=14)
        ).isoformat(),
        "stage": "Sold",
        "switchboard_photo_received": True,
        "electricity_bill_received": True,
        "notes": (
            f"Customer confirmed the roof is {roof}. "
            "Installation access is clear. "
            "No unresolved customer issues reported."
        ),
    }

    # Introduce one intentional QC issue in selected records.
    issue = number % 10

    if issue == 1:
        deal["system_size_kw"] = -2

    elif issue == 2:
        deal["state"] = "XX"

    elif issue == 3:
        deal["roof_type"] = "unknown"

    elif issue == 4:
        deal["payment_type"] = "cash"
        deal["deposit_amount"] = 0

    elif issue == 5:
        deal["signature_date"] = (
            sale_date + timedelta(days=2)
        ).isoformat()

    elif issue == 6:
        deal["requested_install_date"] = (
            sale_date + timedelta(days=3)
        ).isoformat()

    elif issue == 7:
        deal["switchboard_photo_received"] = False

    elif issue == 8:
        deal["postcode"] = "9999"

    elif issue == 9:
        deal["notes"] = (
            f"Customer confirmed the roof is {roof}. "
            "Installation access is blocked and remains unresolved."
        )

    return deal


deals = [create_deal(i) for i in range(1, 101)]

with open(OUTPUT, "w", encoding="utf-8") as file:
    json.dump(deals, file, indent=2)

print(f"Generated {len(deals)} synthetic deals.")
print(f"Saved to: {OUTPUT}")
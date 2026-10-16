import json
import os

import requests
from dotenv import load_dotenv

from backend.integrations.external_qc import run_external_qc

load_dotenv()

HUBSPOT_PROPERTIES = [
    "dealname",
    "amount",
    "description",
    "solarqc_customer_name",
    "solarqc_deal_id",
    "solarqc_deposit_amount",
    "solarqc_installation_date",
    "solarqc_payment_method",
    "solarqc_postcode",
    "solarqc_roof_type",
    "solarqc_sale_date",
    "solarqc_signature_date",
    "solarqc_state",
    "solarqc_system_size_kw",
]


def fetch_hubspot_qc_deal(solarqc_deal_id="DEMO-004"):
    token = os.getenv("HUBSPOT_ACCESS_TOKEN")

    if not token:
        raise ValueError("HUBSPOT_ACCESS_TOKEN is missing.")

    url = "https://api.hubapi.com/crm/v3/objects/deals"

    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}"},
        params={
            "limit": 100,
            "properties": ",".join(HUBSPOT_PROPERTIES),
        },
        timeout=30,
    )

    response.raise_for_status()

    for deal in response.json().get("results", []):
        properties = deal.get("properties", {})

        if properties.get("solarqc_deal_id") == solarqc_deal_id:
            return properties

    raise ValueError(f"SolarQC deal {solarqc_deal_id} not found.")


def normalize_hubspot_qc_deal(properties):
    description = properties.get("description") or "{}"

    try:
        extra = json.loads(description)
    except json.JSONDecodeError as exc:
        raise ValueError("HubSpot Deal Description contains invalid JSON.") from exc

    if not isinstance(extra, dict):
        raise ValueError("HubSpot Deal Description must contain a JSON object.")

    return {
        "deal_id": properties.get("solarqc_deal_id"),
        "customer_name": properties.get("solarqc_customer_name"),
        "state": properties.get("solarqc_state"),
        "postcode": properties.get("solarqc_postcode"),
        "system_size_kw": properties.get("solarqc_system_size_kw"),
        "roof_type": properties.get("solarqc_roof_type"),
        "payment_type": properties.get("solarqc_payment_method"),
        "deposit_amount": properties.get("solarqc_deposit_amount"),
        "total_price": properties.get("amount"),
        "sale_date": properties.get("solarqc_sale_date"),
        "signature_date": properties.get("solarqc_signature_date"),
        "requested_install_date": properties.get("solarqc_installation_date"),
        "contract_received": extra.get("contract_received"),
        "electricity_bill_received": extra.get("electricity_bill_received"),
        "switchboard_photo_received": extra.get("switchboard_photo_received"),
        "notes": extra.get("sales_notes"),
        "stage": extra.get("sales_status"),
    }


def run_hubspot_qc(solarqc_deal_id="DEMO-004"):
    properties = fetch_hubspot_qc_deal(solarqc_deal_id)

    record = normalize_hubspot_qc_deal(properties)

    return run_external_qc(record)
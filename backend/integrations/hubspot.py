import os
import requests


HUBSPOT_API_URL = "https://api.hubapi.com"


def fetch_hubspot_deals(limit=100):
    """Retrieve CRM deals from HubSpot."""

    token = os.getenv("HUBSPOT_ACCESS_TOKEN")

    if not token:
        raise ValueError(
            "HUBSPOT_ACCESS_TOKEN is not configured."
        )

    if not isinstance(limit, int) or not 1 <= limit <= 100:
        raise ValueError("Limit must be between 1 and 100.")

    response = requests.get(
        f"{HUBSPOT_API_URL}/crm/v3/objects/deals",
        headers={
            "Authorization": f"Bearer {token}",
        },
        params={
            "limit": limit,
            "properties": [
                "dealname",
                "amount",
                "dealstage",
                "closedate",
            ],
        },
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    return data.get("results", [])
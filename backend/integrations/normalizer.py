def normalize_google_sheet_deal(record):
    """Convert a Google Sheets row into a SolarQC-style record."""

    if not isinstance(record, dict):
        raise ValueError("Record must be a dictionary.")

    return {
        "deal_id": record.get("deal_id", ""),
        "customer_name": record.get("customer_name", ""),
        "state": record.get("state", ""),
        "postcode": record.get("postcode", ""),
        "roof_type": record.get("roof_type", ""),
        "system_size_kw": record.get("system_size_kw", ""),
        "payment_type": record.get("payment_type", ""),
        "total_price": record.get("total_price", ""),
        "deposit_amount": record.get("deposit_amount", ""),
        "sale_date": record.get("sale_date", ""),
        "signature_date": record.get("signature_date", ""),
        "requested_install_date": record.get(
            "requested_install_date", ""
        ),
        "stage": record.get("stage", ""),
        "switchboard_photo_received": record.get(
            "switchboard_photo_received", ""
        ),
        "electricity_bill_received": record.get(
            "electricity_bill_received", ""
        ),
        "notes": record.get("notes", ""),
    }


def normalize_hubspot_deal(record):
    """Convert standard HubSpot fields into a partial SolarQC record."""

    if not isinstance(record, dict):
        raise ValueError("Record must be a dictionary.")

    properties = record.get("properties") or {}

    return {
        "deal_id": record.get("id", ""),
        "customer_name": properties.get("dealname", ""),
        "total_price": properties.get("amount", ""),
        "stage": properties.get("dealstage", ""),
        "sale_date": properties.get("closedate", ""),
        "source": "hubspot",
        "mapping_status": "PARTIAL",
    }
# SolarQC Integrations

## Google Sheets

Supports read-only retrieval of spreadsheet rows.

Authentication:
- Google service account
- Spreadsheet shared with service account
- Google Sheets API enabled

Current limitations:
- No automatic type conversion
- No schema validation
- No write-back
- No external-record QC execution

## HubSpot

Supports retrieval of CRM deal records.

Authentication:
- HubSpot private app access token
- Required CRM deal read permissions

Current limitations:
- Maximum 100 records per request
- No pagination
- Standard deal properties only
- Partial SolarQC field mapping
- No write-back

## Security

- Use fictional test records.
- Never commit credentials.
- Do not expose integration endpoints publicly without authentication.
- Store secrets outside source control.

## Status

Connectors implemented and mock-tested.
Live authentication not yet verified.
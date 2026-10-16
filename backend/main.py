import json

from fastapi import FastAPI
from ollama import Client
from backend.tools import (
    get_deal,
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
from backend.qc_runner import run_all_qc
from backend.rag_engine import answer_policy_question
from backend.agent_orchestrator import execute_agent
from fastapi import HTTPException

from backend.integrations.google_sheets import (
    fetch_sheet_records,
)

from backend.integrations.hubspot import (
    fetch_hubspot_deals,
)

from backend.integrations.normalizer import (
    normalize_google_sheet_deal,
    normalize_hubspot_deal,
)

from pydantic import BaseModel
from backend.integrations.external_qc import run_external_qc
from fastapi import HTTPException
from backend.integrations.hubspot_qc import run_hubspot_qc
from fastapi import Depends
from backend.security import require_api_key


from backend.integrations.hubspot_writeback import (
    build_qc_note,
    qc_fingerprint,
    create_hubspot_note,
    resolve_hubspot_deal_id,
    find_existing_qc_note,
)









app = FastAPI(title="SolarQC Agent")
protected_integration = {
    "dependencies": [Depends(require_api_key)]
}

# Connect to Ollama running in Docker
ollama_client = Client(host="http://127.0.0.1:11434")


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "project": "SolarQC Agent",
        "version": "0.1.0"
    }


@app.get("/ask")
def ask_qwen(question: str):
    response = ollama_client.chat(
        model="qwen2.5:3b",
        messages=[
            {"role": "user", "content": question}
        ]
    )

    return {
        "model": "qwen2.5:3b",
        "answer": response.message.content
    }


@app.get("/agent")
def run_agent(question: str):

    messages = [
        {
            "role": "system",
            "content": (
                "You are SolarQC, an AI assistant that checks Australian "
                "solar installation sales deals. "
                "Use the available tools to retrieve deal information and "
                "perform quality-control checks. "
                "When a QC tool returns PASS or FAIL, report that exact result. "
                "Never invent QC results or claim a check was completed "
                "without tool evidence. "
                "If information is missing, explain what is missing. "
                "Keep your answers concise."
            )
        },
        {
            "role": "user",
            "content": question
        }
    ]

    # Ask Qwen which tool it wants to use
    response = ollama_client.chat(
        model="qwen2.5:3b",
        messages=messages,
        tools=[get_deal, check_system_size, check_required_fields, check_state, check_roof_type]
        
    )

    messages.append(response.message)

    # Execute tools requested by Qwen
    for tool_call in response.message.tool_calls or []:

        if tool_call.function.name == "get_deal":
            result = get_deal(**tool_call.function.arguments)


        elif tool_call.function.name == "check_state":
            result = check_state(**tool_call.function.arguments)

        elif tool_call.function.name == "check_roof_type":
            result = check_roof_type(**tool_call.function.arguments)
        elif tool_call.function.name == "check_cash_deposit":
            result = check_cash_deposit(**tool_call.function.arguments)
        elif tool_call.function.name == "check_signature_date":
            result = check_signature_date(**tool_call.function.arguments)
        elif tool_call.function.name == "check_install_date":
            result = check_install_date(**tool_call.function.arguments)
        elif tool_call.function.name == "check_sold_documents":
            result = check_sold_documents(**tool_call.function.arguments)
        elif tool_call.function.name == "check_postcode_state":
            result = check_postcode_state(**tool_call.function.arguments)
        

        else:
            continue

        # Return verified QC results directly
        if tool_call.function.name in [
            "check_system_size",
            "check_required_fields",
            "check_state"
            "check_roof_type"
            "check_cash_deposit",
            "check_signature_date",
            "check_install_date",
            "check_sold_documents",
            "check_postcode_state",
        ]:
            return {
                "answer": (
                    f"{result.get('rule', 'QC')}: "

                    f"{result.get('result', 'NEEDS_HUMAN')} - "
                    
                    f"{result.get('reason', result.get('error', 'Review required'))}"
                ),
                "qc_result": result,
                "tools_used": [tool_call.function.name]
            }

        messages.append({
            "role": "tool",
            "tool_name": tool_call.function.name,
            "content": json.dumps(result)
        })

    # Ask Qwen to interpret retrieved information
    final_response = ollama_client.chat(
        model="qwen2.5:3b",
        messages=messages
    )

    return {
        "answer": final_response.message.content,
        "tools_used": [
            call.function.name
            for call in response.message.tool_calls or []
        ]
    }

@app.get("/qc/{deal_id}")
def check_deal_qc(deal_id: str):
    """Run all 11 quality-control checks for one deal."""
    return run_all_qc(deal_id)

from typing import Optional


class AgentRunRequest(BaseModel):
    deal_id: str
    selected_rules: Optional[list[str]] = None


@app.post("/agent/run")
def run_advanced_agent(payload: AgentRunRequest):
    """Run multiple QC tools with policy references."""

    return execute_agent(
        deal_id=payload.deal_id,
        selected_rules=payload.selected_rules,
    )

@app.get("/integrations/google-sheets", **protected_integration)
def get_google_sheet_deals(
    spreadsheet_id: str,
    sheet_range: str = "Sheet1!A1:Z1000",
):
    """Retrieve and normalize Google Sheets records."""

    try:
        records = fetch_sheet_records(
            spreadsheet_id,
            sheet_range,
        )

        return {
            "source": "google_sheets",
            "count": len(records),
            "records": [
                normalize_google_sheet_deal(record)
                for record in records
            ],
        }

    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Unable to retrieve Google Sheets records.",
        )


@app.get("/integrations/hubspot", **protected_integration)
def get_hubspot_deals(limit: int = 100):
    """Retrieve and normalize HubSpot CRM deals."""

    try:
        records = fetch_hubspot_deals(limit)

        return {
            "source": "hubspot",
            "count": len(records),
            "records": [
                normalize_hubspot_deal(record)
                for record in records
            ],
        }

    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Unable to retrieve HubSpot deals.",
        )



@app.post("/integrations/google-sheets/qc", **protected_integration)
def run_google_sheets_qc(
    spreadsheet_id: str,
    sheet_range: str = "Sheet1!A1:P100",
):
    """Run QC on records retrieved from Google Sheets."""

    try:
        records = fetch_sheet_records(
            spreadsheet_id,
            sheet_range,
        )



    except Exception as exc:
        print(
            f"Google Sheets integration error: {type(exc).__name__}: {exc}",
            flush=True,
        )
        raise HTTPException(
            status_code=502,
            detail="Unable to retrieve Google Sheets records.",
        )

    


    

    results = []

    for index, record in enumerate(records, start=2):
        try:
            qc_result = run_external_qc(record)

            results.append(
                {
                    "row": index,
                    "deal_id": record.get("deal_id", ""),
                    "status": "PROCESSED",
                    "qc": qc_result,
                }
            )

        except ValueError as exc:
            results.append(
                {
                    "row": index,
                    "deal_id": record.get("deal_id", ""),
                    "status": "INVALID_RECORD",
                    "error": str(exc),
                }
            )

    return {
        "source": "google_sheets",
        "records_processed": len(results),
        "results": results,
    }


@app.post("/integrations/hubspot/qc", **protected_integration)
def run_hubspot_qc_endpoint(deal_id: str = "DEMO-004"):
    try:
        result = run_hubspot_qc(deal_id)
        return {
            "source": "hubspot",
            "deal_id": deal_id,
            "qc": result,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Unable to process HubSpot QC request.",
        )



@app.post(
    "/integrations/hubspot/qc/writeback",
    **protected_integration,
)
def hubspot_qc_writeback(
    deal_id: str = "DEMO-004",
    dry_run: bool = True,
):
    """
    Evaluate a fictional HubSpot deal and optionally save a QC note.

    Dry-run is the default. Live mode verifies the deal and checks
    for an existing matching note before creating one.
    """

    try:
        qc_result = run_hubspot_qc(deal_id)

        note_body = build_qc_note(deal_id, qc_result)
        fingerprint = qc_fingerprint(deal_id, qc_result)

        if dry_run:
            return {
                "source": "hubspot",
                "deal_id": deal_id,
                "mode": "DRY_RUN",
                "written": False,
                "fingerprint": fingerprint,
                "note_preview": note_body,
                "qc": qc_result,
            }

        hubspot_deal_id = resolve_hubspot_deal_id(deal_id)

        existing_note_id = find_existing_qc_note(
            hubspot_deal_id,
            fingerprint,
        )

        if existing_note_id:
            return {
                "source": "hubspot",
                "deal_id": deal_id,
                "hubspot_deal_id": hubspot_deal_id,
                "mode": "LIVE",
                "written": False,
                "duplicate": True,
                "fingerprint": fingerprint,
                "hubspot_note_id": existing_note_id,
                "qc": qc_result,
            }

        note = create_hubspot_note(
            hubspot_deal_id=hubspot_deal_id,
            note_body=note_body,
        )

        return {
            "source": "hubspot",
            "deal_id": deal_id,
            "hubspot_deal_id": hubspot_deal_id,
            "mode": "LIVE",
            "written": True,
            "duplicate": False,
            "fingerprint": fingerprint,
            "hubspot_note_id": note.get("id"),
            "qc": qc_result,
        }

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Unable to complete HubSpot QC write-back.",
        )
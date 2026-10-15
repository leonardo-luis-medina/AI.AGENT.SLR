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







app = FastAPI(title="SolarQC Agent")

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
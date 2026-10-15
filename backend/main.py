import json

from fastapi import FastAPI
from ollama import Client
from backend.tools import get_deal, check_system_size, check_required_fields




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
        tools=[get_deal, check_system_size, check_required_fields]

        
    )

    messages.append(response.message)

    # Execute tools requested by Qwen
    for tool_call in response.message.tool_calls or []:

        if tool_call.function.name == "get_deal":
            result = get_deal(**tool_call.function.arguments)


        elif tool_call.function.name == "check_required_fields":
            result = check_required_fields(**tool_call.function.arguments)


        

        else:
            continue

        # Return verified QC results directly
        if tool_call.function.name in ["check_system_size", "check_required_fields"]:
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
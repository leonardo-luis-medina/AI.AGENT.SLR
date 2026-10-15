import json
from ollama import Client

client = Client(host="http://127.0.0.1:11434")


def analyze_deal_notes(deal: dict) -> dict:
    """Evaluate R10 and R11 using Qwen."""

    if not isinstance(deal.get("notes"), str) or not deal["notes"].strip():
        return {
            "R10": {
                "result": "NEEDS_HUMAN",
                "reason": "Deal notes are missing."
            },
            "R11": {
                "result": "NEEDS_HUMAN",
                "reason": "Deal notes are missing."
            }
        }

    prompt = f"""
You are reviewing a fictional Australian solar sales deal.

Evaluate these rules:

R10: Identify unresolved red flags involving cancellation,
asbestos, installation access, or customer disputes.

R11: Identify contradictions between the written notes
and structured deal fields.

Return PASS, FAIL, or NEEDS_HUMAN for each rule.

Rules:
- PASS only when supported by the available evidence.
- FAIL when a clear issue is present.
- NEEDS_HUMAN when information is ambiguous.



- Do not invent facts.
- For R11, compare explicit statements in the notes against
  the structured deal fields.
- If the notes explicitly contradict a structured field,
  return FAIL, not NEEDS_HUMAN.
- Example: roof_type="tile" but notes say "roof is metal"
  means R11=FAIL.
- Return exactly this JSON structure:
  {{
    "R10": {{"result": "PASS or FAIL or NEEDS_HUMAN", "reason": "explanation"}},
    "R11": {{"result": "PASS or FAIL or NEEDS_HUMAN", "reason": "explanation"}}
  }}

Deal:
{json.dumps(deal)}
"""

    response = client.chat(
        model="qwen2.5:3b",
        messages=[
            {"role": "user", "content": prompt}
        ],
        format="json"
    )

    try:
        results = json.loads(response.message.content)

        notes = deal["notes"].lower()

        unresolved_access = (
            "access is blocked" in notes
            or "access remains unresolved" in notes
            or "access issue unresolved" in notes
        )

        if unresolved_access:
            results["R10"] = {
                "result": "FAIL",
                "reason": "Sales notes explicitly indicate an unresolved installation access issue."
            }

                # R11: Detect explicit roof-type contradictions.
        roof_type = deal.get("roof_type", "").lower()

        roof_types = ("tile", "metal", "concrete")

        mentioned_roofs = [
            roof
            for roof in roof_types
            if (
                f"roof is {roof}" in notes
                or f"roof is made of {roof}" in notes
            )
        ]

        if (
            roof_type in roof_types
            and len(mentioned_roofs) == 1
            and mentioned_roofs[0] != roof_type
        ):
            results["R11"] = {
                "result": "FAIL",
                "reason": (
                    f"Roof-type contradiction: structured field says "
                    f"'{roof_type}', but notes explicitly say "
                    f"'{mentioned_roofs[0]}'."
                )
            }
        




        return results





    
    except (json.JSONDecodeError, TypeError):
        return {
            "R10": {
                "result": "NEEDS_HUMAN",
                "reason": "AI response could not be validated."
            },
            "R11": {
                "result": "NEEDS_HUMAN",
                "reason": "AI response could not be validated."
            }
        }
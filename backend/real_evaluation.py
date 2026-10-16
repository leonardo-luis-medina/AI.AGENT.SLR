from datetime import datetime, timezone

from backend.evaluation import evaluate_predictions
from backend.integrations.external_qc import run_external_qc


def evaluate_real_agent(cases, qc_runner=None):
    """
    Evaluate SolarQC using actual QC engine predictions.

    Expected labels come from the evaluation dataset.
    Predicted labels come from the QC engine.

    The dataset must not supply predicted_status.
    """

    if not isinstance(cases, list):
        raise ValueError("Evaluation cases must be a list.")

    if qc_runner is None:
        qc_runner = run_external_qc

    predictions = []
    seen_ids = set()

    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise ValueError(
                f"Case {index} must be a dictionary."
            )

        deal = case.get("deal")

        if not isinstance(deal, dict):
            raise ValueError(
                f"Case {index} must contain a deal dictionary."
            )

        deal_id = str(deal.get("deal_id", "")).strip()

        if not deal_id:
            raise ValueError(
                f"Case {index} is missing deal_id."
            )

        if deal_id in seen_ids:
            raise ValueError(
                f"Duplicate deal_id: {deal_id}"
            )

        seen_ids.add(deal_id)

        if "predicted_status" in case:
            raise ValueError(
                "Do not manually supply predicted_status."
            )

        expected_status = case.get("expected_status")

        qc_result = qc_runner(deal)

        if not isinstance(qc_result, dict):
            raise ValueError(
                f"QC engine returned an invalid result for {deal_id}."
            )

        predicted_status = qc_result.get("overall_status")

        predictions.append(
            {
                "deal_id": deal_id,
                "expected_status": expected_status,
                "predicted_status": predicted_status,
            }
        )

    metrics = evaluate_predictions(predictions)

    return {
        "evaluation_type": "real_qc_engine",
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "dataset_type": "fictional_labeled_deals",
        "predictions": predictions,
        "metrics": metrics,
        "limitations": [
            "Uses fictional solar sales scenarios.",
            "Expected labels are defined independently of the QC engine.",
            "Small evaluation datasets do not establish production accuracy.",
            "Results are not regulatory certifications.",
        ],
    }
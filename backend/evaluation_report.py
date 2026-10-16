import json
from datetime import datetime, timezone
from pathlib import Path

from backend.evaluation import evaluate_predictions


DEFAULT_REPORT_DIR = Path("data/evaluation")


def generate_evaluation_report(
    cases: list[dict],
    output_dir=DEFAULT_REPORT_DIR,
) -> dict:
    """
    Evaluate labeled cases and save a JSON report.
    """

    metrics = evaluate_predictions(cases)

    report = {
        "report_type": "SolarQC Decision Evaluation",
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "dataset_type": "fictional_labeled_cases",
        "metrics": metrics,
        "limitations": [
            "Uses fictional solar sales scenarios.",
            "Evaluates decision labels, not regulatory compliance.",
            "Results depend on the quality of expected labels.",
            "Small datasets may not represent real-world performance.",
        ],
    }

    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)

    report_path = directory / "latest_evaluation.json"

    report_path.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    return report
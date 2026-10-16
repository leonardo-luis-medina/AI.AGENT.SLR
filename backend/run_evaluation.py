import argparse
import json
from pathlib import Path

from backend.evaluation_report import generate_evaluation_report


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate SolarQC decision predictions."
    )

    parser.add_argument(
        "--dataset",
        default="data/evaluation/labeled_cases.json",
    )

    args = parser.parse_args()

    dataset_path = Path(args.dataset)

    if not dataset_path.exists():
        raise SystemExit(
            f"Dataset not found: {dataset_path}"
        )

    cases = json.loads(
        dataset_path.read_text(encoding="utf-8")
    )

    report = generate_evaluation_report(cases)

    print("\nSolarQC Evaluation Report")
    print("=========================")

    metrics = report["metrics"]

    print(f"Cases: {metrics['total_cases']}")
    print(f"Accuracy: {metrics['accuracy']:.2%}")
    print(
        f"False-pass rate: "
        f"{metrics['false_pass_rate']:.2%}"
    )
    print(
        f"PASS precision: "
        f"{metrics['pass_precision']:.2%}"
    )
    print(
        f"PASS recall: "
        f"{metrics['pass_recall']:.2%}"
    )
    print(
        f"Human-review rate: "
        f"{metrics['human_review_rate']:.2%}"
    )

    print(
        "\nReport saved to: "
        "data/evaluation/latest_evaluation.json"
    )


if __name__ == "__main__":
    main()
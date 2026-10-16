import argparse
import json
from pathlib import Path

from backend.real_evaluation import evaluate_real_agent


DEFAULT_DATASET = Path(
    "data/evaluation/real_agent_cases.json"
)

DEFAULT_REPORT = Path(
    "data/evaluation/latest_real_agent_evaluation.json"
)


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate actual SolarQC QC engine decisions."
    )

    parser.add_argument(
        "--dataset",
        default=str(DEFAULT_DATASET),
    )

    parser.add_argument(
        "--output",
        default=str(DEFAULT_REPORT),
    )

    args = parser.parse_args()

    dataset_path = Path(args.dataset)

    cases = json.loads(
        dataset_path.read_text(encoding="utf-8")
    )

    report = evaluate_real_agent(cases)

    output_path = Path(args.output)
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(report, indent=2, default=str),
        encoding="utf-8",
    )

    metrics = report["metrics"]

    print("\nSolarQC — Real Agent Evaluation")
    print("================================")
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

    print("\nIndividual predictions:")

    for prediction in report["predictions"]:
        print(
            f"  {prediction['deal_id']}: "
            f"expected={prediction['expected_status']}, "
            f"actual={prediction['predicted_status']}"
        )

    print(f"\nReport saved to: {output_path}")


if __name__ == "__main__":
    main()
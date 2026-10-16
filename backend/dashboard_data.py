import json
from collections import Counter
from pathlib import Path

import pandas as pd


DEFAULT_HISTORY = Path("data/monitoring/qc_history.jsonl")


def load_qc_history(history_file=DEFAULT_HISTORY):
    """Load successfully processed QC evaluations."""

    path = Path(history_file)

    if not path.exists():
        return []

    entries = []

    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            try:
                entry = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON on history line {line_number}"
                ) from exc

            if not isinstance(entry, dict):
                raise ValueError(
                    f"Invalid history entry on line {line_number}"
                )

            if entry.get("status") == "PROCESSED":
                entries.append(entry)

    return entries


def build_dashboard_metrics(entries):
    """Calculate evaluation-level QC metrics."""

    statuses = Counter()

    for entry in entries:
        qc = entry.get("qc", {})

        if not isinstance(qc, dict):
            continue

        status = str(
            qc.get("overall_status", "UNKNOWN")
        ).upper()

        statuses[status] += 1

    return {
        "total_evaluations": sum(statuses.values()),
        "passed": statuses["PASS"],
        "failed": statuses["FAIL"],
        "needs_human": statuses["NEEDS_HUMAN"],
        "unknown": statuses["UNKNOWN"],
    }


def build_evaluation_table(entries):
    """Build a table of historical QC evaluations."""

    rows = []

    for entry in entries:
        qc = entry.get("qc", {})

        if not isinstance(qc, dict):
            qc = {}

        summary = qc.get("summary", {})

        if not isinstance(summary, dict):
            summary = {}

        rows.append(
            {
                "timestamp": entry.get("timestamp"),
                "deal_id": entry.get("deal_id"),
                "change_type": entry.get("change_type"),
                "overall_status": qc.get(
                    "overall_status", "UNKNOWN"
                ),
                "pass_count": summary.get("PASS", 0),
                "fail_count": summary.get("FAIL", 0),
                "human_review_count": summary.get(
                    "NEEDS_HUMAN", 0
                ),
            }
        )

    return pd.DataFrame(
        rows,
        columns=[
            "timestamp",
            "deal_id",
            "change_type",
            "overall_status",
            "pass_count",
            "fail_count",
            "human_review_count",
        ],
    )


def build_rule_metrics(entries):
    """Count outcomes for each QC rule."""

    counts = {}

    for entry in entries:
        qc = entry.get("qc", {})

        if not isinstance(qc, dict):
            continue

        results = qc.get("results", [])

        if not isinstance(results, list):
            continue

        for result in results:
            if not isinstance(result, dict):
                continue

            rule = str(
                result.get(
                    "rule",
                    result.get("rule_id", "UNKNOWN"),
                )
            )

            status = str(
                result.get("status", "UNKNOWN")
            ).upper()

            if rule not in counts:
                counts[rule] = Counter()

            counts[rule][status] += 1

    rows = []

    for rule, outcomes in sorted(counts.items()):
        rows.append(
            {
                "rule": rule,
                "PASS": outcomes["PASS"],
                "FAIL": outcomes["FAIL"],
                "NEEDS_HUMAN": outcomes["NEEDS_HUMAN"],
            }
        )

    return pd.DataFrame(
        rows,
        columns=[
            "rule",
            "PASS",
            "FAIL",
            "NEEDS_HUMAN",
        ],
    )
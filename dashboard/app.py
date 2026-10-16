from pathlib import Path
import json
import sys

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from backend.dashboard_data import (
    load_qc_history,
    build_dashboard_metrics,
    build_evaluation_table,
    build_rule_metrics,
)


HISTORY_FILE = PROJECT_ROOT / "data/monitoring/qc_history.jsonl"

EVALUATION_FILE = (
    PROJECT_ROOT
    / "data/evaluation/latest_real_agent_evaluation.json"
)

STATE_FILE = (
    PROJECT_ROOT
    / "data/monitoring/sheet_state.json"
)


st.set_page_config(
    page_title="SolarQC | AI Quality Control",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded",
)


def apply_styles():
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1450px;
        }

        h1, h2, h3 {
            letter-spacing: -0.02em;
        }

        div[data-testid="stMetric"] {
            background-color: rgba(128, 128, 128, 0.06);
            border: 1px solid rgba(128, 128, 128, 0.16);
            border-radius: 12px;
            padding: 16px;
        }

        div[data-testid="stMetricLabel"] {
            font-weight: 600;
        }

        section[data-testid="stSidebar"] {
            border-right: 1px solid rgba(128, 128, 128, 0.15);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def load_json_report(path):
    if not path.exists():
        return None

    try:
        with path.open("r", encoding="utf-8") as file:
            report = json.load(file)
    except (OSError, json.JSONDecodeError):
        return None

    return report if isinstance(report, dict) else None


def format_percentage(value):
    if not isinstance(value, (int, float)):
        return "N/A"

    return f"{value:.1%}"


def show_overview(entries):
    st.header("Quality Control Overview")
    st.caption(
        "Historical QC evaluations from the SolarQC monitoring engine."
    )

    metrics = build_dashboard_metrics(entries)

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Evaluations",
        metrics["total_evaluations"],
    )

    col2.metric(
        "Passed",
        metrics["passed"],
    )

    col3.metric(
        "Failed",
        metrics["failed"],
    )

    col4.metric(
        "Human Review",
        metrics["needs_human"],
    )

    st.divider()

    history_df = build_evaluation_table(entries)

    if history_df.empty:
        st.info(
            "No QC monitoring history is available yet. "
            "Run the Google Sheets monitor to generate results."
        )
        return

    left, right = st.columns(2)

    with left:
        st.subheader("QC Decision Distribution")

        status_counts = (
            history_df["overall_status"]
            .fillna("UNKNOWN")
            .value_counts()
        )

        st.bar_chart(status_counts)

    with right:
        st.subheader("Evaluation Activity")

        trend_df = history_df.copy()

        trend_df["timestamp"] = pd.to_datetime(
            trend_df["timestamp"],
            errors="coerce",
            utc=True,
        )

        trend_df = trend_df.dropna(
            subset=["timestamp"]
        )

        if not trend_df.empty:
            daily_counts = (
                trend_df.groupby(
                    trend_df["timestamp"].dt.date
                )
                .size()
            )

            st.line_chart(daily_counts)
        else:
            st.info("No valid timestamps available.")

    st.divider()

    st.subheader("Recent QC Evaluations")

    recent_df = history_df.copy()

    recent_df["sort_timestamp"] = pd.to_datetime(
        recent_df["timestamp"],
        errors="coerce",
        utc=True,
    )

    recent_df = recent_df.sort_values(
        "sort_timestamp",
        ascending=False,
    )

    recent_df = recent_df.drop(
        columns=["sort_timestamp"]
    )

    st.dataframe(
        recent_df.head(10),
        use_container_width=True,
        hide_index=True,
    )


def show_deal_monitoring(entries):
    st.header("Deal Monitoring")
    st.caption(
        "Search and review historical SolarQC evaluations."
    )

    history_df = build_evaluation_table(entries)

    if history_df.empty:
        st.info("No historical deal evaluations found.")
        return

    search = st.text_input(
        "Search Deal ID",
        placeholder="Example: DEMO-001",
    )

    status_options = sorted(
        history_df["overall_status"]
        .dropna()
        .unique()
        .tolist()
    )

    selected_statuses = st.multiselect(
        "Filter by QC Status",
        options=status_options,
        default=status_options,
    )

    filtered_df = history_df.copy()

    if search.strip():
        filtered_df = filtered_df[
            filtered_df["deal_id"]
            .fillna("")
            .astype(str)
            .str.contains(
                search.strip(),
                case=False,
                regex=False,
            )
        ]

    filtered_df = filtered_df[
        filtered_df["overall_status"].isin(
            selected_statuses
        )
    ]

    st.metric(
        "Matching Evaluations",
        len(filtered_df),
    )

    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True,
    )

    if not filtered_df.empty:
        csv_data = filtered_df.to_csv(index=False)

        st.download_button(
            "Download Filtered History (CSV)",
            data=csv_data,
            file_name="solarqc_filtered_history.csv",
            mime="text/csv",
        )


def show_ai_evaluation():
    st.header("AI Evaluation")
    st.caption(
        "Measured results from the fictional labeled-deal benchmark."
    )

    report = load_json_report(EVALUATION_FILE)

    if report is None:
        st.warning(
            "No real-agent evaluation report found. "
            "Run: python -m backend.run_real_evaluation"
        )
        return

    metrics = report.get("metrics", {})

    if not isinstance(metrics, dict):
        st.error("The evaluation report has an invalid metrics format.")
        return

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Evaluation Cases",
        metrics.get("total_cases", 0),
    )

    col2.metric(
        "Accuracy",
        format_percentage(
            metrics.get("accuracy")
        ),
    )

    col3.metric(
        "False-Pass Rate",
        format_percentage(
            metrics.get("false_pass_rate")
        ),
    )

    col4.metric(
        "Human-Review Rate",
        format_percentage(
            metrics.get("human_review_rate")
        ),
    )

    st.divider()

    left, right = st.columns(2)

    with left:
        st.subheader("PASS Classification")

        st.metric(
            "PASS Precision",
            format_percentage(
                metrics.get("pass_precision")
            ),
        )

        st.metric(
            "PASS Recall",
            format_percentage(
                metrics.get("pass_recall")
            ),
        )

        st.metric(
            "False-Pass Count",
            metrics.get("false_pass_count", 0),
        )

    with right:
        st.subheader("Confusion Matrix")

        confusion_matrix = metrics.get(
            "confusion_matrix", {}
        )

        if isinstance(confusion_matrix, dict) and confusion_matrix:
            matrix_df = pd.DataFrame.from_dict(
                confusion_matrix,
                orient="index",
            )

            matrix_df.index.name = "Expected"

            st.dataframe(
                matrix_df,
                use_container_width=True,
            )

            st.caption(
                "Rows represent expected decisions; "
                "columns represent actual agent predictions."
            )
        else:
            st.info("No confusion matrix available.")

    st.divider()

    st.subheader("Individual Evaluation Results")

    predictions = report.get("predictions", [])

    if isinstance(predictions, list) and predictions:
        predictions_df = pd.DataFrame(predictions)

        if {
            "expected_status",
            "predicted_status",
        }.issubset(predictions_df.columns):
            predictions_df["correct"] = (
                predictions_df["expected_status"]
                == predictions_df["predicted_status"]
            )

        st.dataframe(
            predictions_df,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No individual predictions available.")

    st.info(
        "These metrics describe performance on a small, "
        "fictional evaluation dataset. They do not establish "
        "production accuracy or regulatory compliance."
    )


def show_rule_analytics(entries):
    st.header("QC Rule Analytics")
    st.caption(
        "Rule-level outcomes across recorded QC evaluations."
    )

    rule_df = build_rule_metrics(entries)

    if rule_df.empty:
        st.info("No rule-level evaluation results found.")
        return

    total_failures = int(rule_df["FAIL"].sum())

    total_reviews = int(
        rule_df["NEEDS_HUMAN"].sum()
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Rules Observed",
        len(rule_df),
    )

    col2.metric(
        "Rule Failures",
        total_failures,
    )

    col3.metric(
        "Human-Review Triggers",
        total_reviews,
    )

    st.divider()

    st.subheader("Rule Outcomes")

    st.dataframe(
        rule_df,
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Rules Requiring Attention")

    attention_df = rule_df.set_index("rule")[
        ["FAIL", "NEEDS_HUMAN"]
    ]

    st.bar_chart(attention_df)

    st.caption(
        "Counts represent rule outcomes across evaluations, "
        "not unique deals."
    )


def show_system_status(entries):
    st.header("System Status")
    st.caption(
        "Local SolarQC monitoring and evaluation resources."
    )

    evaluation_exists = EVALUATION_FILE.exists()
    history_exists = HISTORY_FILE.exists()
    state_exists = STATE_FILE.exists()

    st.subheader("Local Resources")

    resources = pd.DataFrame(
        [
            {
                "Component": "QC Monitoring History",
                "Status": (
                    "Available"
                    if history_exists
                    else "Not Found"
                ),
            },
            {
                "Component": "Monitoring State",
                "Status": (
                    "Available"
                    if state_exists
                    else "Not Found"
                ),
            },
            {
                "Component": "Real-Agent Evaluation Report",
                "Status": (
                    "Available"
                    if evaluation_exists
                    else "Not Found"
                ),
            },
        ]
    )

    st.dataframe(
        resources,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.subheader("Monitoring Summary")

    st.metric(
        "Stored QC Evaluations",
        len(entries),
    )

    st.info(
        "Resource availability does not indicate that "
        "Google Sheets, HubSpot, or automatic monitoring "
        "is currently connected or running."
    )

    st.subheader("Technology Stack")

    st.markdown(
        """
        - **AI Engine:** Local Ollama / Qwen
        - **Backend:** Python and FastAPI
        - **Frontend:** Streamlit
        - **Data Processing:** Pandas
        - **Integrations:** Google Sheets and HubSpot
        - **Testing:** Pytest and GitHub Actions
        """
    )


def main():
    apply_styles()

    with st.sidebar:
        st.title("☀️ SolarQC")

        st.caption(
            "AI-Assisted Solar Sales Quality Control"
        )

        st.divider()

        page = st.radio(
            "Navigation",
            [
                "Overview",
                "Deal Monitoring",
                "AI Evaluation",
                "Rule Analytics",
                "System Status",
            ],
        )

        st.divider()

        if st.button("Refresh Dashboard"):
            st.rerun()

        st.caption("Portfolio Demonstration")
        st.caption("Fictional Australian Solar Sales Data")

    entries = load_qc_history(HISTORY_FILE)

    if page == "Overview":
        show_overview(entries)

    elif page == "Deal Monitoring":
        show_deal_monitoring(entries)

    elif page == "AI Evaluation":
        show_ai_evaluation()

    elif page == "Rule Analytics":
        show_rule_analytics(entries)

    elif page == "System Status":
        show_system_status(entries)

    st.divider()

    st.caption(
        "SolarQC is an AI-assisted portfolio demonstration "
        "using fictional sales data and illustrative QC rules. "
        "Results are not regulatory certifications."
    )


if __name__ == "__main__":
    main()
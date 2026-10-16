from pathlib import Path
import json
import sys

import pandas as pd
import streamlit as st
from backend.demo_config import is_public_demo


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from backend.dashboard_data import (
    load_qc_history,
    build_dashboard_metrics,
    build_evaluation_table,
    build_rule_metrics,
)

from backend.interactive_qc import (
    get_sample_deals,
    run_interactive_qc,
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






def show_interactive_qc():
    st.header("Interactive Quality Check")

    st.caption(
        "Evaluate fictional Australian solar sales deals "
        "using SolarQC's existing quality control rules."
    )

    if is_public_demo():
        st.info(
            "Public Demo Mode: SolarQC evaluates nine "
            "deterministic quality control rules. "
            "No local AI model or external CRM connection "
            "is required."
        )
    else:
        st.info(
            "Deterministic Mode evaluates nine QC rules "
            "without Ollama. Full AI Mode evaluates all "
            "eleven rules using your configured local AI."
        )

    samples = get_sample_deals()

    selected_sample = st.selectbox(
        "Choose a Fictional Sample Deal",
        options=list(samples.keys()),
    )

    sample = samples[selected_sample]




    mode_options = [
        "Deterministic Demo — 9 Rules",
    ]

    if not is_public_demo():
        mode_options.append(
            "Full AI — 11 Rules (Requires Ollama)"
        )

    mode_label = st.radio(
        "Execution Mode",
        mode_options,
)





    mode = (
        "deterministic"
        if mode_label.startswith("Deterministic")
        else "full_ai"
    )

    st.divider()

    with st.form("interactive_qc_form"):
        st.subheader("Deal Information")

        deal_id = st.text_input(
            "Deal ID",
            value=sample["deal_id"],
        )

        customer_name = st.text_input(
            "Fictional Customer Name",
            value=sample["customer_name"],
        )

        col1, col2 = st.columns(2)

        with col1:
            state = st.selectbox(
                "State",
                ["NSW", "VIC", "QLD", "SA", "WA", "TAS", "ACT", "NT"],
                index=[
                    "NSW", "VIC", "QLD", "SA",
                    "WA", "TAS", "ACT", "NT",
                ].index(sample["state"]),
            )

            postcode = st.text_input(
                "Postcode",
                value=str(sample["postcode"]),
            )

            roof_type = st.text_input(
                "Roof Type",
                value=sample["roof_type"],
            )

            system_size_kw = st.number_input(
                "System Size (kW)",
                min_value=0.0,
                value=float(sample["system_size_kw"]),
                step=0.1,
            )

        with col2:
            payment_type = st.selectbox(
                "Payment Type",
                ["cash", "finance"],
                index=(
                    0
                    if sample["payment_type"] == "cash"
                    else 1
                ),
            )

            total_price = st.number_input(
                "Total Price (AUD)",
                min_value=0.0,
                value=float(sample["total_price"]),
                step=100.0,
            )

            deposit_amount = st.number_input(
                "Deposit Amount (AUD)",
                min_value=0.0,
                value=float(sample["deposit_amount"]),
                step=100.0,
            )

            stage = st.text_input(
                "Deal Stage",
                value=sample["stage"],
            )

        sale_date = st.date_input(
            "Sale Date",
            value=pd.to_datetime(
                sample["sale_date"]
            ).date(),
        )

        signature_date = st.date_input(
            "Signature Date",
            value=pd.to_datetime(
                sample["signature_date"]
            ).date(),
        )

        requested_install_date = st.date_input(
            "Requested Installation Date",
            value=pd.to_datetime(
                sample["requested_install_date"]
            ).date(),
        )

        switchboard_photo_received = st.checkbox(
            "Switchboard Photo Received",
            value=sample["switchboard_photo_received"],
        )

        electricity_bill_received = st.checkbox(
            "Electricity Bill Received",
            value=sample["electricity_bill_received"],
        )

        notes = st.text_area(
            "Deal Notes",
            value=sample["notes"],
        )

        submitted = st.form_submit_button(
            "Run Quality Check",
            use_container_width=True,
        )

    if not submitted:
        return

    deal = {
        "deal_id": deal_id,
        "customer_name": customer_name,
        "state": state,
        "postcode": postcode,
        "roof_type": roof_type,
        "system_size_kw": system_size_kw,
        "payment_type": payment_type,
        "total_price": total_price,
        "deposit_amount": deposit_amount,
        "sale_date": sale_date.isoformat(),
        "signature_date": signature_date.isoformat(),
        "requested_install_date": (
            requested_install_date.isoformat()
        ),
        "stage": stage,
        "switchboard_photo_received": (
            switchboard_photo_received
        ),
        "electricity_bill_received": (
            electricity_bill_received
        ),
        "notes": notes,
    }

    try:
        with st.spinner("Running SolarQC checks..."):
            evaluation = run_interactive_qc(
                deal,
                mode=mode,
            )

    except (ValueError, TypeError) as exc:
        st.error(f"Unable to evaluate deal: {exc}")
        return

    qc = evaluation["qc"]

    status = qc.get("overall_status", "UNKNOWN")
    summary = qc.get("summary", {})

    st.divider()
    st.subheader("Quality Control Result")

    if status == "PASS":
        st.success("QC Decision: PASS")

    elif status == "FAIL":
        st.error("QC Decision: FAIL")

    elif status == "NEEDS_HUMAN":
        st.warning("QC Decision: NEEDS HUMAN REVIEW")

    else:
        st.info(f"QC Decision: {status}")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Rules Evaluated",
        qc.get("rules_executed", 0),
    )

    col2.metric(
        "Passed",
        summary.get("PASS", 0),
    )

    col3.metric(
        "Failed",
        summary.get("FAIL", 0),
    )

    col4.metric(
        "Human Review",
        summary.get("NEEDS_HUMAN", 0),
    )

    results = qc.get("results", [])

    if results:
        st.subheader("Rule-Level Findings")

        rows = []

        for result in results:
            policy = result.get("policy") or {}

            rows.append(
                {
                    "Rule": result.get("rule"),
                    "Decision": result.get("result"),
                    "Reason": result.get("reason"),
                    "Policy": policy.get("title", ""),
                }
            )

        st.dataframe(
            pd.DataFrame(rows),
            use_container_width=True,
            hide_index=True,
        )

    st.caption(
        "This evaluation uses fictional data and "
        "illustrative policies. It is not a regulatory "
        "certification or installation approval."
    )










def main():
    apply_styles()

    with st.sidebar:
        st.title("☀️ SolarQC")

        st.caption(
            "AI-Assisted Solar Sales Quality Control"
        )

        st.divider()

        if is_public_demo():
            navigation_pages = [
                "Overview",
                "Interactive QC",
            ]
        else:
            navigation_pages = [
                "Overview",
                "Interactive QC",
                "Deal Monitoring",
                "AI Evaluation",
                "Rule Analytics",
                "System Status",
            ]

        page = st.radio(
            "Navigation",
            navigation_pages,
        )

        st.divider()

        if st.button("Refresh Dashboard"):
            st.rerun()

        st.caption("Portfolio Demonstration")
        st.caption("Fictional Australian Solar Sales Data")

    entries = (
        []
        if is_public_demo()
        else load_qc_history(HISTORY_FILE)
    )


    if page == "Overview":
        show_overview(entries)

    elif page == "Interactive QC":
        show_interactive_qc()

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
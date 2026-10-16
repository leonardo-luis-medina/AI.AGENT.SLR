from pathlib import Path
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


st.set_page_config(
    page_title="SolarQC | AI Quality Control",
    page_icon="☀️",
    layout="wide",
)


st.title("☀️ SolarQC")
st.caption(
    "AI-Assisted Solar Sales Quality Control | "
    "Australian Fictional Sales Data"
)

st.divider()

entries = load_qc_history()

if not entries:
    st.warning(
        "No QC monitoring history found. "
        "Run the Google Sheets monitor first."
    )
    st.stop()


metrics = build_dashboard_metrics(entries)

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "QC Evaluations",
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

st.subheader("QC Evaluation History")

history_df = build_evaluation_table(entries)

deal_options = sorted(
    history_df["deal_id"].dropna().unique().tolist()
)

selected_deals = st.multiselect(
    "Filter by Deal",
    options=deal_options,
    default=deal_options,
)

filtered_df = history_df[
    history_df["deal_id"].isin(selected_deals)
]

st.dataframe(
    filtered_df,
    use_container_width=True,
    hide_index=True,
)


st.divider()

left, right = st.columns(2)

with left:
    st.subheader("QC Status Distribution")

    status_counts = (
        filtered_df["overall_status"]
        .value_counts()
    )

    if not status_counts.empty:
        st.bar_chart(status_counts)
    else:
        st.info("No matching evaluations.")


with right:
    st.subheader("QC Evaluations Over Time")

    trend_df = filtered_df.copy()

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
        st.info("No timestamp data available.")


st.divider()

st.subheader("QC Rule Performance")

selected_entry_ids = {
    str(deal_id) for deal_id in selected_deals
}

filtered_entries = [
    entry
    for entry in entries
    if str(entry.get("deal_id")) in selected_entry_ids
]

rule_df = build_rule_metrics(filtered_entries)

if not rule_df.empty:
    st.dataframe(
        rule_df,
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Rule Failures")

    failure_chart = rule_df.set_index("rule")[
        ["FAIL", "NEEDS_HUMAN"]
    ]

    st.bar_chart(failure_chart)

else:
    st.info("No rule-level results available.")


st.divider()

st.caption(
    "SolarQC is a portfolio demonstration using "
    "fictional sales data and illustrative QC rules. "
    "Results are not regulatory certifications."
)
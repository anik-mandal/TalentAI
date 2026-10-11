"""
pages/analytics_page.py — Analytics Dashboard
"""

import streamlit as st
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.db import get_supabase
from shared.ui_theme import apply_theme

apply_theme()

supabase = get_supabase()

# -------------------------------------------------
# HEADER
# -------------------------------------------------

st.markdown("<h1>📈 Analytics Dashboard</h1>", unsafe_allow_html=True)
st.caption("Recruitment pipeline performance metrics and insights")
st.divider()

# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------

try:
    jobs = supabase.table("jobs").select("*").execute().data or []
    candidates = supabase.table("candidates").select("*").execute().data or []
except Exception as e:
    st.error(f"⚠️ Could not connect to Supabase: {e}")
    st.warning("Please verify your SUPABASE_URL and SUPABASE_KEY in your .env or Streamlit Secrets.")
    st.stop()

jobs_df = pd.DataFrame(jobs)
candidates_df = pd.DataFrame(candidates)

if candidates_df.empty:
    st.info("No data available for analytics yet. Start by posting jobs and receiving applications.")
    st.stop()

# -------------------------------------------------
# TOP METRICS
# -------------------------------------------------

total = len(candidates_df)
shortlisted = len(candidates_df[candidates_df["status"] == "shortlisted"])
rejected = len(candidates_df[candidates_df["status"] == "rejected"])
maybe = len(candidates_df[candidates_df["status"] == "maybe"])
applied = len(candidates_df[candidates_df["status"] == "applied"])

screened = total - applied
shortlist_rate = round((shortlisted / screened * 100), 1) if screened > 0 else 0
rejection_rate = round((rejected / screened * 100), 1) if screened > 0 else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("👥 Total Candidates", total)
col2.metric("✅ Shortlist Rate", f"{shortlist_rate}%")
col3.metric("❌ Rejection Rate", f"{rejection_rate}%")
col4.metric("📩 Pending Screening", applied)

st.divider()

# -------------------------------------------------
# CHARTS
# -------------------------------------------------

try:
    import plotly.express as px

    # -----------------------------------------------
    # CANDIDATES PER JOB
    # -----------------------------------------------

    st.subheader("📊 Candidates per Job")

    if "job_applied" in candidates_df.columns:
        per_job = candidates_df["job_applied"].value_counts().reset_index()
        per_job.columns = ["Job", "Candidates"]

        fig = px.bar(
            per_job,
            x="Job",
            y="Candidates",
            color="Candidates",
            color_continuous_scale=["#6c63ff", "#a855f7"],
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e8e8f0"),
            xaxis=dict(gridcolor="#1a1a2e"),
            yaxis=dict(gridcolor="#1a1a2e"),
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # -----------------------------------------------
    # STATUS DISTRIBUTION
    # -----------------------------------------------

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📉 Status Distribution")

        status_counts = candidates_df["status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]

        color_map = {
            "applied": "#6c63ff",
            "shortlisted": "#4ade80",
            "maybe": "#facc15",
            "rejected": "#f87171",
            "interview_scheduled": "#38bdf8",
        }

        fig = px.pie(
            status_counts,
            names="Status",
            values="Count",
            color="Status",
            color_discrete_map=color_map,
            hole=0.4,
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e8e8f0"),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("📊 Hiring Funnel")

        funnel_data = {
            "Stage": ["Applied", "Screened", "Shortlisted", "Maybe", "Rejected"],
            "Count": [applied, screened, shortlisted, maybe, rejected]
        }

        fig = px.funnel(
            funnel_data, x="Count", y="Stage",
            color_discrete_sequence=["#6c63ff"]
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e8e8f0"),
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # -----------------------------------------------
    # COMPANY-WISE ANALYTICS
    # -----------------------------------------------

    if not jobs_df.empty and "company_name" in jobs_df.columns:
        st.subheader("🏢 Jobs per Company")

        company_jobs = jobs_df["company_name"].value_counts().reset_index()
        company_jobs.columns = ["Company", "Jobs"]

        fig = px.bar(
            company_jobs,
            x="Company",
            y="Jobs",
            color="Jobs",
            color_continuous_scale=["#a855f7", "#6c63ff"],
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e8e8f0"),
            xaxis=dict(gridcolor="#1a1a2e"),
            yaxis=dict(gridcolor="#1a1a2e"),
        )
        st.plotly_chart(fig, use_container_width=True)

    # -----------------------------------------------
    # SCORE DISTRIBUTION
    # -----------------------------------------------

    if "screening_score" in candidates_df.columns:

        scored = candidates_df[candidates_df["screening_score"].notna()]

        if not scored.empty:
            st.divider()
            st.subheader("📊 Screening Score Distribution")

            fig = px.histogram(
                scored,
                x="screening_score",
                nbins=20,
                color_discrete_sequence=["#6c63ff"],
                labels={"screening_score": "Screening Score"},
            )
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#e8e8f0"),
                xaxis=dict(gridcolor="#1a1a2e"),
                yaxis=dict(gridcolor="#1a1a2e"),
            )
            st.plotly_chart(fig, use_container_width=True)


except ImportError:
    st.warning("Install `plotly` for interactive charts: `pip install plotly`")

    # Fallback: show raw numbers
    st.subheader("Pipeline Summary")

    st.markdown(f"""
    | Metric | Count |
    |--------|-------|
    | Total Candidates | {total} |
    | Applied | {applied} |
    | Shortlisted | {shortlisted} |
    | Maybe | {maybe} |
    | Rejected | {rejected} |
    | Shortlist Rate | {shortlist_rate}% |
    | Rejection Rate | {rejection_rate}% |
    """)

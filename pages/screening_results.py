"""
pages/screening_results.py — Detailed Screening Results
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

st.markdown("<h1>📋 Screening Results</h1>", unsafe_allow_html=True)
st.caption("View detailed AI screening analysis for each candidate")
st.divider()

# -------------------------------------------------
# SELECT JOB
# -------------------------------------------------

try:
    jobs = supabase.table("jobs").select("id, job_title, company_name").execute().data
except Exception as e:
    st.error(f"⚠️ Could not connect to Supabase: {e}")
    st.warning("Please verify your SUPABASE_URL and SUPABASE_KEY in your .env or Streamlit Secrets.")
    st.stop()

if not jobs:
    st.warning("No jobs posted yet.")
    st.stop()

job_map = {
    f"{j['job_title']} at {j['company_name']} (ID: {j['id']})": j["id"]
    for j in jobs
}

selected = st.selectbox("Select Job", list(job_map.keys()))
job_id = job_map[selected]

# -------------------------------------------------
# LOAD RESULTS
# -------------------------------------------------

data = (
    supabase.table("candidates")
    .select(
        "name, email, screening_score, skills_matched, "
        "skills_missing, culture_fit, recommendation, "
        "screening_reason, status"
    )
    .eq("job_id", job_id)
    .order("screening_score", desc=True)
    .execute()
)

candidates = data.data

if not candidates:
    st.info("No screened candidates yet for this job.")
else:

    df = pd.DataFrame(candidates)

    # -------------------------------------------------
    # METRICS
    # -------------------------------------------------

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "✅ Shortlisted",
        len(df[df["status"] == "shortlisted"])
    )

    c2.metric(
        "🤔 Maybe",
        len(df[df["status"] == "maybe"])
    )

    c3.metric(
        "❌ Rejected",
        len(df[df["status"] == "rejected"])
    )

    st.divider()

    # -------------------------------------------------
    # RESULTS TABLE
    # -------------------------------------------------

    st.subheader("Detailed Results")

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "screening_score": st.column_config.ProgressColumn(
                "Score",
                min_value=0,
                max_value=100,
                format="%d"
            ),
            "name": "Candidate",
            "status": "Status",
            "skills_matched": "Skills Matched",
            "skills_missing": "Skills Missing",
            "culture_fit": "Culture Fit",
            "recommendation": "AI Recommendation",
            "screening_reason": "Screening Explanation",
        }
    )

    # -------------------------------------------------
    # INDIVIDUAL CARDS
    # -------------------------------------------------

    st.divider()
    st.subheader("📝 Individual Analysis")

    for _, row in df.iterrows():

        score = row.get("screening_score", 0) or 0
        status = row.get("status", "unknown")

        if status == "shortlisted":
            border_color = "#4ade80"
            bg_color = "#0d2b1a"
        elif status == "rejected":
            border_color = "#f87171"
            bg_color = "#2b0d0d"
        else:
            border_color = "#facc15"
            bg_color = "#2b2b0d"

        st.markdown(f"""
        <div style='background: {bg_color}; border: 1px solid {border_color};
                    border-radius: 12px; padding: 1.2rem; margin-bottom: 1rem;'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <strong style='font-size: 1.1rem;'>{row.get("name", "N/A")}</strong>
                <span style='color: {border_color}; font-weight: 600;'>
                    {score}/100 — {status.upper()}
                </span>
            </div>
            <div style='color: #a0a0c0; margin-top: 0.5rem; font-size: 0.9rem;'>
                {row.get("screening_reason", row.get("recommendation", "No explanation available"))}
            </div>
            <div style='margin-top: 0.5rem; font-size: 0.85rem;'>
                <span style='color: #4ade80;'>✓ {row.get("skills_matched", "N/A")}</span>
                &nbsp;|&nbsp;
                <span style='color: #f87171;'>✗ {row.get("skills_missing", "N/A")}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)


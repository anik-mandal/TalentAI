"""
pages/hr_dashboard.py — HR Dashboard Overview
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

st.markdown("<h1>📊 HR Dashboard</h1>", unsafe_allow_html=True)
st.caption("Real-time overview of your recruitment pipeline")
st.divider()

# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------

try:
    jobs = supabase.table("jobs").select("*").execute().data or []
    candidates = supabase.table("candidates").select("*").execute().data or []
    slots = supabase.table("interview_slots").select("*").execute().data or []
except Exception as e:
    st.error(f"⚠️ Could not connect to Supabase: {e}")
    st.warning("Please verify your SUPABASE_URL and SUPABASE_KEY in your .env (local) or Streamlit Secrets (cloud).")
    st.stop()

jobs_df = pd.DataFrame(jobs)
candidates_df = pd.DataFrame(candidates)
slots_df = pd.DataFrame(slots)

# -------------------------------------------------
# METRICS
# -------------------------------------------------

total_jobs = len(jobs_df)
total_candidates = len(candidates_df)
scheduled = len(slots_df[slots_df["is_booked"] == True]) if not slots_df.empty else 0
available = len(slots_df[slots_df["is_booked"] == False]) if not slots_df.empty else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("🏢 Open Positions", total_jobs)
col2.metric("👥 Total Candidates", total_candidates)
col3.metric("📅 Scheduled Interviews", scheduled)
col4.metric("🟢 Available Slots", available)

st.divider()

# -------------------------------------------------
# STATUS BREAKDOWN
# -------------------------------------------------

if not candidates_df.empty:

    st.subheader("Pipeline Status")

    applied = len(candidates_df[candidates_df["status"] == "applied"])
    shortlisted = len(candidates_df[candidates_df["status"] == "shortlisted"])
    maybe = len(candidates_df[candidates_df["status"] == "maybe"])
    rejected = len(candidates_df[candidates_df["status"] == "rejected"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📩 Applied", applied)
    c2.metric("✅ Shortlisted", shortlisted)
    c3.metric("🤔 Maybe", maybe)
    c4.metric("❌ Rejected", rejected)

    st.divider()

# -------------------------------------------------
# TOP CANDIDATES
# -------------------------------------------------

    st.subheader("🏆 Top AI-Ranked Candidates")

    top = candidates_df.sort_values(
        by="screening_score", ascending=False
    ).head(10)

    display_cols = [
        "name", "job_applied", "screening_score",
        "skills_matched", "recommendation", "status"
    ]

    available_cols = [c for c in display_cols if c in top.columns]

    st.dataframe(
        top[available_cols],
        use_container_width=True,
        hide_index=True
    )

else:
    st.info("No candidates in the system yet. Start by posting jobs and inviting applications.")

# -------------------------------------------------
# RECENT JOBS
# -------------------------------------------------

if not jobs_df.empty:
    st.divider()
    st.subheader("📝 Recent Job Postings")

    display_cols = ["job_title", "company_name", "location", "experience_years", "salary_range"]
    available_cols = [c for c in display_cols if c in jobs_df.columns]

    st.dataframe(
        jobs_df[available_cols].head(10),
        use_container_width=True,
        hide_index=True
    )

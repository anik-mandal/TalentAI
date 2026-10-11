"""
pages/candidate_database.py — Candidate Database with Filters
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

st.markdown("<h1>👥 Candidate Database</h1>", unsafe_allow_html=True)
st.caption("Search and filter all candidates across your hiring pipeline")
st.divider()

# -------------------------------------------------
# LOAD DATA
# -------------------------------------------------

try:
    candidates = supabase.table("candidates").select("*").execute().data or []
except Exception as e:
    st.error(f"⚠️ Could not connect to Supabase: {e}")
    st.warning("Please verify your SUPABASE_URL and SUPABASE_KEY in your .env or Streamlit Secrets.")
    st.stop()

if not candidates:
    st.info("No candidates in the database yet.")
    st.stop()

df = pd.DataFrame(candidates)

# -------------------------------------------------
# METRICS
# -------------------------------------------------

total = len(df)
shortlisted = len(df[df["status"] == "shortlisted"]) if "status" in df.columns else 0
maybe = len(df[df["status"] == "maybe"]) if "status" in df.columns else 0
rejected = len(df[df["status"] == "rejected"]) if "status" in df.columns else 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("👥 Total", total)
col2.metric("✅ Shortlisted", shortlisted)
col3.metric("🤔 Maybe", maybe)
col4.metric("❌ Rejected", rejected)

st.divider()

# -------------------------------------------------
# FILTERS
# -------------------------------------------------

col_search, col_job, col_status = st.columns(3)

with col_search:
    search_name = st.text_input("🔍 Search by Name", placeholder="Enter candidate name...")

with col_job:
    job_values = ["All Jobs"]
    if "job_applied" in df.columns:
        job_values += sorted(df["job_applied"].dropna().unique().tolist())
    filter_job = st.selectbox("Filter by Job", job_values)

with col_status:
    status_values = ["All Statuses", "applied", "shortlisted", "maybe", "rejected", "interview_scheduled"]
    filter_status = st.selectbox("Filter by Status", status_values)

# -------------------------------------------------
# APPLY FILTERS
# -------------------------------------------------

filtered = df.copy()

if search_name:
    filtered = filtered[
        filtered["name"].str.contains(search_name, case=False, na=False)
    ]

if filter_job != "All Jobs" and "job_applied" in filtered.columns:
    filtered = filtered[filtered["job_applied"] == filter_job]

if filter_status != "All Statuses" and "status" in filtered.columns:
    filtered = filtered[filtered["status"] == filter_status]

# -------------------------------------------------
# TABLE
# -------------------------------------------------

st.markdown(f"**Showing {len(filtered)} of {total} candidates**")

display_cols = [
    "name", "email", "phone", "job_applied",
    "status", "screening_score", "recommendation"
]

available_cols = [c for c in display_cols if c in filtered.columns]

st.dataframe(
    filtered[available_cols].sort_values(
        by="screening_score", ascending=False, na_position="last"
    ) if "screening_score" in available_cols else filtered[available_cols],
    use_container_width=True,
    hide_index=True
)

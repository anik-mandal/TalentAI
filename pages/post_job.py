"""
pages/post_job.py — Post New Job with Unique Rule
"""

import streamlit as st
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.db import get_supabase
from shared.chroma_setup import store_job_in_chroma
from shared.ui_theme import apply_theme

apply_theme()

supabase = get_supabase()

# -------------------------------------------------
# HEADER
# -------------------------------------------------

st.markdown("<h1>📝 Post New Job</h1>", unsafe_allow_html=True)
st.caption("Create a new job posting — it will be available for candidates to apply")
st.divider()

# -------------------------------------------------
# JOB FORM
# -------------------------------------------------

with st.form("job_form"):

    col1, col2 = st.columns(2)

    with col1:
        company_name = st.text_input("Company Name *")
        job_title = st.text_input("Job Title *")
        location = st.text_input("Location")
        salary_range = st.text_input("Salary Range")

    with col2:
        experience = st.selectbox(
            "Experience Required",
            ["0-1 years", "1-3 years", "3-5 years", "5-10 years", "10+ years"]
        )
        skills_required = st.text_area("Required Skills *")
        requirements = st.text_area("Job Description *")

    submitted = st.form_submit_button("🚀 Create Job Posting", use_container_width=True)


# -------------------------------------------------
# FORM HANDLING
# -------------------------------------------------

if submitted:

    if not company_name or not job_title or not skills_required or not requirements:
        st.error("Please fill all required fields.")
        st.stop()

    # -------------------------------------------------
    # UNIQUE JOB RULE: (company_name + job_title) must be unique
    # -------------------------------------------------

    existing = (
        supabase.table("jobs")
        .select("id")
        .eq("company_name", company_name.strip())
        .eq("job_title", job_title.strip())
        .execute()
    )

    if existing.data:
        st.error(
            f"⚠️ A job posting for **{job_title}** at **{company_name}** already exists. "
            f"Each (company + job title) combination must be unique."
        )
        st.stop()

    # -------------------------------------------------
    # INSERT TO SUPABASE
    # -------------------------------------------------

    with st.spinner("Creating job posting..."):

        job_data = {
            "company_name": company_name.strip(),
            "job_title": job_title.strip(),
            "skills_required": skills_required.strip(),
            "requirements": requirements.strip(),
            "experience_years": experience,
            "location": location.strip(),
            "salary_range": salary_range.strip(),
            "created_at": datetime.now().isoformat()
        }

        result = supabase.table("jobs").insert(job_data).execute()

        if result.data:
            job_id = result.data[0]["id"]

            # Store in ChromaDB for RAG
            job_text = f"""
Company: {company_name}
Job Title: {job_title}
Skills Required: {skills_required}
Requirements: {requirements}
Experience: {experience}
Location: {location}
Salary: {salary_range}
"""
            store_job_in_chroma(job_id, job_text)

            st.success(f"✅ Job posted successfully! (ID: {job_id})")
            st.balloons()
        else:
            st.error("Failed to create job posting. Please try again.")


# -------------------------------------------------
# EXISTING JOBS
# -------------------------------------------------

st.divider()
st.subheader("📋 Existing Job Postings")

jobs = supabase.table("jobs").select("id, job_title, company_name, location, experience_years").execute().data

if jobs:
    st.dataframe(jobs, use_container_width=True, hide_index=True)
else:
    st.info("No jobs posted yet.")

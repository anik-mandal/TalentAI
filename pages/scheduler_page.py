"""
pages/scheduler_page.py — Interview Scheduler
HR: Create slots + view schedule
Candidate: Book available slots
"""

import streamlit as st
from datetime import datetime, date
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.db import get_supabase
from shared.ui_theme import apply_theme

apply_theme()

supabase = get_supabase()

portal = st.query_params.get("portal") or st.session_state.get("portal", "candidate")

# -------------------------------------------------
# HEADER
# -------------------------------------------------

st.markdown("<h1>📅 Interview Scheduler</h1>", unsafe_allow_html=True)
st.divider()


# =================================================
# HR VIEW
# =================================================

if portal == "hr":

    tabs = st.tabs(["📅 Scheduled Interviews", "➕ Create Slots"])

    # -----------------------------------------------
    # VIEW SCHEDULE
    # -----------------------------------------------

    with tabs[0]:

        st.subheader("Scheduled Interviews")

        slots = supabase.table("interview_slots").select("*").execute().data or []

        if not slots:
            st.info("No interview slots created yet.")
        else:
            import pandas as pd
            df = pd.DataFrame(slots)

            booked = df[df["is_booked"] == True]
            available = df[df["is_booked"] == False]

            col1, col2 = st.columns(2)
            col1.metric("✅ Booked", len(booked))
            col2.metric("🟢 Available", len(available))

            if not booked.empty:
                st.markdown("**Booked Interviews:**")
                display_cols = ["date", "time", "interviewer_name", "candidate_name"]
                avail_cols = [c for c in display_cols if c in booked.columns]
                st.dataframe(booked[avail_cols], use_container_width=True, hide_index=True)

            if not available.empty:
                st.markdown("**Available Slots:**")
                display_cols = ["date", "time", "interviewer_name"]
                avail_cols = [c for c in display_cols if c in available.columns]
                st.dataframe(available[avail_cols], use_container_width=True, hide_index=True)

    # -----------------------------------------------
    # CREATE SLOTS
    # -----------------------------------------------

    with tabs[1]:

        st.subheader("Create Interview Slots")

        with st.form("create_slots"):

            interviewer = st.text_input("Interviewer Name *")
            interview_date = st.date_input("Date", min_value=date.today())

            times = st.multiselect(
                "Time Slots",
                ["9:00 AM", "10:00 AM", "11:00 AM", "12:00 PM",
                 "2:00 PM", "3:00 PM", "4:00 PM", "5:00 PM"]
            )

            submitted = st.form_submit_button(
                "Create Slots", use_container_width=True
            )

        if submitted:

            if not interviewer or not times:
                st.error("Please fill in the interviewer name and select at least one time slot.")
            else:

                for t in times:

                    slot = {
                        "date": str(interview_date),
                        "time": t,
                        "interviewer_name": interviewer.strip(),
                        "is_booked": False,
                        "candidate_id": None,
                        "candidate_name": None,
                        "created_at": datetime.now().isoformat()
                    }

                    supabase.table("interview_slots").insert(slot).execute()

                st.success(f"✅ {len(times)} interview slots created!")


# =================================================
# CANDIDATE VIEW
# =================================================

else:

    st.caption("Enter your email to view and book available interview slots")

    email_input = st.text_input("Your Email Address")

    if not email_input:
        st.stop()

    # Fetch candidate
    result = (
        supabase.table("candidates")
        .select("*")
        .eq("email", email_input)
        .execute()
    )

    if not result.data:
        st.error("Email not found. Please apply for a job first.")
        st.stop()

    candidate = result.data[0]

    # Status checks
    if candidate["status"] == "interview_scheduled":
        st.success("✅ You already have an interview booked! Check your Telegram for details.")
        st.stop()

    if candidate["status"] not in ["shortlisted", "maybe"]:
        st.info("🕐 You are not yet eligible to book an interview. Your application is under review.")
        st.stop()

    st.success(f"Welcome **{candidate['name']}**! Please choose an interview slot below.")

    # Fetch available slots
    slots = (
        supabase.table("interview_slots")
        .select("*")
        .eq("is_booked", False)
        .execute().data
    )

    if not slots:
        st.warning("No interview slots available right now. HR will contact you on Telegram.")
        st.stop()

    # Slot selection
    slot_labels = {
        f"📅 {s['date']} | ⏰ {s['time']} | 👤 {s['interviewer_name']}": s
        for s in slots
    }

    chosen_label = st.selectbox("Available Slots", list(slot_labels.keys()))
    chosen_slot = slot_labels[chosen_label]

    st.markdown("")

    if st.button("✅ Confirm This Interview Slot", use_container_width=True):

        with st.spinner("Booking your slot..."):

            # Mark slot as booked
            supabase.table("interview_slots").update({
                "is_booked": True,
                "candidate_id": candidate["id"],
                "candidate_name": candidate["name"]
            }).eq("id", chosen_slot["id"]).execute()

            # Update candidate status
            supabase.table("candidates").update({
                "status": "interview_scheduled"
            }).eq("id", candidate["id"]).execute()

            # Send Telegram confirmation
            try:
                from engagement.telegram_notifier import send_interview_confirmation

                send_interview_confirmation(
                    candidate_name=candidate["name"],
                    chat_id=candidate.get("telegram_chat_id"),
                    interviewer_name=chosen_slot["interviewer_name"],
                    date=chosen_slot["date"],
                    time=chosen_slot["time"],
                    job_title=candidate.get("job_applied", "")
                )
            except Exception:
                pass

            st.success("🎉 Interview confirmed!")

            st.markdown(f"""
            <div style='background: #0d2b1a; border: 1px solid #166534;
                        border-radius: 12px; padding: 1.2rem 1.5rem; margin-top: 1rem;'>
                <div style='color: #4ade80; font-weight: 600; margin-bottom: 0.5rem;'>
                    Booking Confirmed
                </div>
                <div style='color: #e8e8f0;'>
                    📅 {chosen_slot['date']} at {chosen_slot['time']}
                </div>
                <div style='color: #e8e8f0;'>
                    👤 Interviewer: {chosen_slot['interviewer_name']}
                </div>
                <div style='color: #7878a0; font-size: 0.85rem; margin-top: 0.5rem;'>
                    A Telegram message has been sent with full details.
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.balloons()

import streamlit as st
import sys
import os

# allow importing shared modules
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from shared.db import get_supabase
from engagement.telegram_notifier import send_interview_confirmation
from dotenv import load_dotenv

load_dotenv()

supabase = get_supabase()

# -----------------------------
# Page Configuration
# -----------------------------
st.set_page_config(
    page_title="Book Interview",
    page_icon="📅",
    layout="centered"
)

# -----------------------------
# Styling
# -----------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background: #0a0a0f;
    color: #e8e8f0;
}

h1 {
    font-family: 'Syne', sans-serif !important;
    font-weight: 800 !important;
    color: #ffffff !important;
}

[data-testid="stTextInput"] input {
    background: #13131f !important;
    border: 1px solid #2a2a3e !important;
    border-radius: 10px !important;
    color: #e8e8f0 !important;
}

[data-testid="stSelectbox"] > div {
    background: #13131f !important;
    border: 1px solid #2a2a3e !important;
    border-radius: 10px !important;
    color: #e8e8f0 !important;
}

.stButton > button {
    background: linear-gradient(135deg, #6c63ff, #a855f7) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.65rem 1.5rem !important;
    width: 100% !important;
}

.main .block-container {
    background: #0a0a0f;
    padding: 2rem;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Page Title
# -----------------------------
st.markdown("<h1>📅 Book Interview Slot</h1>", unsafe_allow_html=True)

st.markdown(
"<p style='color:#7878a0;'>Enter your email to view available interview slots</p>",
unsafe_allow_html=True
)

# -----------------------------
# Email Input
# -----------------------------
email_input = st.text_input("Your Email Address")

if not email_input:
    st.stop()

# -----------------------------
# Fetch Candidate
# -----------------------------
result = supabase.table("candidates") \
    .select("*") \
    .eq("email", email_input) \
    .execute()

if not result.data:
    st.error("Email not found. Please apply first.")
    st.stop()

candidate = result.data[0]

# -----------------------------
# Status Checks
# -----------------------------
if candidate["status"] == "interview_scheduled":
    st.success("You already have an interview booked. Check your Telegram for details.")
    st.stop()

if candidate["status"] not in ["shortlisted", "maybe"]:
    st.info("You are not yet eligible to book. Your application is under review.")
    st.stop()

st.success(f"Welcome **{candidate['name']}**! Please choose an interview slot below.")

# -----------------------------
# Fetch Available Slots
# -----------------------------
slots = supabase.table("interview_slots") \
    .select("*") \
    .eq("is_booked", False) \
    .execute().data

if not slots:
    st.warning("No slots available right now. HR will contact you on Telegram.")
    st.stop()

# -----------------------------
# Slot Selection
# -----------------------------
slot_labels = {
    f"📅 {s['date']} | ⏰ {s['time']} | 👤 {s['interviewer_name']}": s
    for s in slots
}

chosen_label = st.selectbox(
    "Available Slots",
    list(slot_labels.keys())
)

chosen_slot = slot_labels[chosen_label]

st.markdown("")

# -----------------------------
# Confirm Button
# -----------------------------
if st.button("Confirm This Interview Slot"):

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

        # Send Telegram message
        send_interview_confirmation(
            candidate_name=candidate["name"],
            chat_id=candidate.get("telegram_chat_id"),
            interviewer_name=chosen_slot["interviewer_name"],
            date=chosen_slot["date"],
            time=chosen_slot["time"],
            job_title=candidate["job_applied"]
        )

        st.success("Interview confirmed!")

        st.markdown(f"""
<div style='background: #0d2b1a;
border: 1px solid #166534;
border-radius: 12px;
padding: 1.2rem 1.5rem;
margin-top: 1rem;'>

<div style='color: #4ade80;
font-weight: 600;
margin-bottom: 0.5rem;'>
Booking Confirmed
</div>

<div style='color: #e8e8f0;'>
📅 {chosen_slot['date']} at {chosen_slot['time']}
</div>

<div style='color: #e8e8f0;'>
👤 Interviewer: {chosen_slot['interviewer_name']}
</div>

<div style='color: #7878a0;
font-size: 0.85rem;
margin-top: 0.5rem;'>
A Telegram message has been sent with full details.
</div>

</div>
""", unsafe_allow_html=True)

        st.balloons()
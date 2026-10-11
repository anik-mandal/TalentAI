"""
pages/chatbot_page.py — AI HR Chatbot
"""

import streamlit as st
import os
import sys
from dotenv import load_dotenv
from groq import Groq

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.db import get_supabase, get_secret
from shared.chroma_setup import get_jobs_collection
from shared.ui_theme import apply_theme

apply_theme()
load_dotenv()

# -------------------------------------------------
# INITIALIZATION
# -------------------------------------------------

GROQ_API_KEY = get_secret("GROQ_API_KEY")

if not GROQ_API_KEY:
    st.error("Missing GROQ_API_KEY. Add it to .env (local) or Streamlit Secrets (cloud).")
    st.stop()

client = Groq(api_key=GROQ_API_KEY)
supabase = get_supabase()
chroma = get_jobs_collection()

# -------------------------------------------------
# SESSION STATE
# -------------------------------------------------

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

if "chat_candidate" not in st.session_state:
    st.session_state.chat_candidate = None

# -------------------------------------------------
# HEADER
# -------------------------------------------------

st.markdown("<h1>🤖 AI HR Assistant</h1>", unsafe_allow_html=True)
st.caption("Ask questions about your job application, interview process, or role requirements.")
st.divider()

# -------------------------------------------------
# EMAIL INPUT
# -------------------------------------------------

email = st.text_input("Enter your email to get started")

if email and st.session_state.chat_candidate is None:

    try:
        result = (
            supabase.table("candidates")
            .select("*")
            .eq("email", email)
            .execute()
        )
        candidate_data = result.data
    except Exception:
        st.error("Database connection error.")
        st.stop()

    if not candidate_data:
        st.error("Email not found in our system. Please apply for a job first.")
        st.stop()

    candidate = candidate_data[0]
    st.session_state.chat_candidate = candidate

# -------------------------------------------------
# CANDIDATE CONTEXT
# -------------------------------------------------

if st.session_state.chat_candidate:

    candidate = st.session_state.chat_candidate
    name = candidate.get("name", "Candidate")
    job_applied = candidate.get("job_applied", "Unknown Role")
    status = candidate.get("status", "unknown")

    st.success(f"Welcome **{name}**!")

    # Sidebar info
    with st.sidebar:
        st.subheader("Candidate Info")
        st.markdown(f"**Name:** {name}")
        st.markdown(f"**Role:** {job_applied}")
        st.markdown(f"**Status:** {status}")

    # Interview booking prompt
    if status in ["shortlisted", "maybe"]:
        st.info("🎉 You are eligible for an interview! Visit the **Interview Scheduler** page to book a slot.")

    st.divider()

    # -------------------------------------------------
    # CHAT HISTORY
    # -------------------------------------------------

    for msg in st.session_state.chat_messages:
        avatar = "👤" if msg["role"] == "user" else "🤖"
        with st.chat_message(msg["role"], avatar=avatar):
            st.write(msg["content"])

    # -------------------------------------------------
    # CHAT INPUT
    # -------------------------------------------------

    question = st.chat_input("Ask something about the job...")

    if question:

        st.session_state.chat_messages.append({
            "role": "user",
            "content": question
        })

        with st.chat_message("user", avatar="👤"):
            st.write(question)

        with st.spinner("Thinking..."):

            # Get job context from ChromaDB
            context = ""
            try:
                results = chroma.query(
                    query_texts=[job_applied],
                    n_results=1
                )
                if results and results.get("documents"):
                    context = results["documents"][0][0]
            except Exception:
                context = ""

            system_prompt = f"""
You are an AI HR assistant for TalentAI recruitment platform.

Use the job description below to answer candidate questions accurately.

JOB DETAILS:
{context}

CANDIDATE STATUS: {status}

Rules:
- Be helpful and professional
- Be concise and clear
- Only answer questions related to the job and recruitment process
- If you don't know, say so honestly
"""

            try:
                response = client.chat.completions.create(
                    model="openai/gpt-oss-120b",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": question}
                    ],
                    temperature=0.3
                )
                answer = response.choices[0].message.content
            except Exception:
                answer = "Sorry, I couldn't generate a response right now. Please try again."

        with st.chat_message("assistant", avatar="🤖"):
            st.write(answer)

        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": answer
        })

        # Log to DB
        try:
            supabase.table("chat_logs").insert({
                "email": email,
                "question": question,
                "answer": answer
            }).execute()
        except Exception:
            pass

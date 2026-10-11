# 🚀 TalentAI — Intelligent Talent Acquisition System

An end-to-end **AI-powered recruitment automation platform** that streamlines candidate sourcing, resume screening, and hiring workflows using **Generative AI, Multi-Agent Systems, and Retrieval-Augmented Generation (RAG)**.

---

## 🌐 Live Demo

🔗 https://talent-acquisition-system-kkpw5w9rk38qnfbydupabt.streamlit.app/

## 📦 Repository

🔗 https://github.com/budhadityaghosh/talent-acquisition-system

---

## 📄 Documentation

* 📎 **Project Report:** [View Full Report](./TalentAI_Academic_Report.docx)

---

# 🧠 Project Overview

TalentAI automates the **entire recruitment lifecycle**, reducing manual effort and eliminating bias using an intelligent AI pipeline.

### ✨ What makes it powerful?

* Multi-agent AI system (CrewAI)
* Context-aware screening using RAG
* Bias-free evaluation pipeline
* Fully automated hiring workflow

---

# 🎯 Key Features

## 👨‍💼 HR Portal

* Post and manage job listings
* Trigger AI screening pipeline
* View real-time dashboard
* Analyze candidate performance
* Schedule interviews

## 👩‍💻 Candidate Portal

* Apply for jobs with resume upload
* AI-powered HR chatbot
* Track application progress
* Book interview slots
* Receive Telegram notifications

## 🤖 AI Pipeline (Core System)

### 🔹 Agent 1 — Sourcing Specialist

* Evaluates candidate profiles
* Assigns quality score (0–100)
* Filters unqualified candidates

### 🔹 Agent 2 — Screening Expert (RAG)

* Retrieves job-specific context from ChromaDB
* Evaluates resumes against requirements
* Outputs structured JSON:

  * screening_score
  * skills_matched
  * skills_missing
  * recommendation

### 🔹 Agent 3 — Engagement Coordinator

* Generates HR reports
* Identifies top candidates
* Suggests hiring actions

---

# 🧱 System Architecture

## 🖼️ Architecture Diagram

```text
+-------------------+        +-------------------+        +----------------------+
|   HR Portal       |        |  Candidate Portal |        |  Telegram Bot System |
|-------------------|        |-------------------|        |----------------------|
| - Post Jobs       |        | - Apply for Job   |        | - Shortlist Alerts   |
| - Run Pipeline    |        | - Upload Resume   |        | - Interview Confirm  |
| - Dashboard       |        | - Chatbot         |        | - Notifications      |
+--------+----------+        +--------+----------+        +----------+-----------+
         |                            |                              |
         +------------+---------------+--------------+---------------+
                      |                              |
                      v                              v
             +-------------------------------+
             |        AI PIPELINE            |
             |-------------------------------|
             | Agent 1: Sourcing             |
             | Agent 2: RAG Screening        |
             | Agent 3: Engagement           |
             | Bias Filter Module            |
             | Groq LLM (Inference Engine)   |
             +---------------+---------------+
                             |
                             v
        +---------------------------------------------+
        |             DATABASE LAYER                  |
        |---------------------------------------------|
        | Supabase (PostgreSQL)                      |
        | ChromaDB (Vector DB for RAG)               |
        +---------------------------------------------+
```

---

## 🧩 Architecture Explanation

### 1. Presentation Layer

* **HR Portal (Streamlit):** Recruiter dashboard
* **Candidate Portal:** Job application interface

---

### 2. AI Processing Layer

* **Agent 1:** Candidate sourcing & filtering
* **Agent 2:** Resume screening using RAG
* **Agent 3:** Engagement report generation

---

### 3. Bias Filtering Layer

Removes:

* Name
* Gender
* Location
* University

✔ Ensures fair and unbiased hiring

---

### 4. Data Layer

#### 🗄️ Supabase (PostgreSQL)

* jobs
* candidates
* interview_slots
* chat_logs

#### 🧠 ChromaDB

* Job embeddings (for RAG)
* Candidate embeddings

---

### 5. Communication Layer

* Telegram Bot integration
* Real-time alerts and notifications

---

# 🧠 Generative AI Implementation

## 🔍 Retrieval-Augmented Generation (RAG)

* Job descriptions embedded into vector DB
* Retrieved dynamically during screening
* Ensures accurate and context-aware scoring

---

## 🤖 Multi-Agent Orchestration

* Built using CrewAI
* Sequential agent execution
* Database-driven workflow

---

## 📦 Structured JSON Output

* Machine-readable LLM responses
* Reliable pipeline integration
* Fallback handling for errors

---

# ⚙️ Tech Stack

| Layer         | Technology       |
| ------------- | ---------------- |
| Frontend      | Streamlit        |
| LLM API       | Groq (LLaMA 3)   |
| Agents        | CrewAI + LiteLLM |
| Backend DB    | Supabase         |
| Vector DB     | ChromaDB         |
| Notifications | Telegram Bot API |
| Parsing       | PyPDF2           |
| Analytics     | Plotly + Pandas  |

---

# 🚀 How to Run Locally

```bash
git clone https://github.com/budhadityaghosh/talent-acquisition-system
cd talent-acquisition-system
pip install -r requirements.txt
streamlit run app.py
```

---

# 📊 Results

* Fully automated recruitment workflow
* Real-time dashboard updates
* Improved screening accuracy with RAG
* Bias-free evaluation system
* Zero-cost deployment (free-tier tools)

---

# 🔮 Future Scope

* LinkedIn integration for real candidate sourcing
* Advanced embedding models
* Multi-stage interview workflows
* Feedback-based model improvement

---

# 👨‍💻 Contributors

* Anik Mandal
* Aryak Pal
* Aswint Guha
* Budhaditya Ghosh

---

# 📌 License

This project is developed for academic purposes under Generative AI coursework.

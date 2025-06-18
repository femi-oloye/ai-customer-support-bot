# app.py

import streamlit as st
from dotenv import load_dotenv
import os
import tempfile
import requests
from openai import OpenAI
from rag import load_and_index_pdf, ask_doc_question
from agent import agent

# --- Load API keys ---
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

# --- UI Config ---
st.set_page_config(page_title="AI Support Bot", layout="centered")
st.title("🟢 WhatsBot - AI Customer Support Assistant")

with st.expander("ℹ️ About", expanded=False):
    st.markdown("""
    This assistant provides:
    - 🤖 GPT-powered chat support  
    - 📄 Q&A from uploaded docs  
    - 📡 CRM info via Airtable  
    - 👨‍💼 Human escalation to Slack  
    """)

# --- Collect Customer Info ---
if "name" not in st.session_state or "email" not in st.session_state:
    with st.form("user_info_form"):
        st.subheader("👤 Enter Your Details")
        name = st.text_input("Full Name")
        email = st.text_input("Email Address")
        submitted = st.form_submit_button("Start Chat")
        if submitted:
            if not name or not email:
                st.warning("Please enter both name and email to continue.")
            else:
                st.session_state.name = name
                st.session_state.email = email
                st.success("✅ You're now connected to the support bot!")
    st.stop()

# --- PDF Upload Section ---
st.markdown("### 📄 Upload Internal Docs")
uploaded_file = st.file_uploader("Upload manual / policy / FAQ (PDF)", type="pdf")

vectordb = None
if uploaded_file:
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name
        vectordb = load_and_index_pdf(tmp_path)
        st.success("✅ Document indexed successfully!")
    except Exception as e:
        st.error(f"❌ Failed to process PDF: {e}")

# --- Chat UI ---
st.markdown("---")
st.markdown("### 💬 Chat with Support")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input("You:", key="user_input")
    submitted = st.form_submit_button("Send")

escalation_keywords = ["refund", "cancel", "human", "talk to agent", "real person", "complain", "not happy", "escalate"]

if submitted and user_input:
    st.session_state.chat_history.append(("user", user_input))

    if any(word in user_input.lower() for word in escalation_keywords):
        bot_reply = f"🔔 Escalation triggered! Our support team will reach out to you shortly."

        # Send escalation to Slack
        try:
            slack_message = {
                "text": (
                    f"🚨 *Customer Escalation Triggered*\n"
                    f"*Name:* {st.session_state.name}\n"
                    f"*Email:* {st.session_state.email}\n"
                    f"*Message:* {user_input}"
                )
            }
            requests.post(SLACK_WEBHOOK_URL, json=slack_message)
        except Exception as e:
            bot_reply += f"\n⚠️ Slack error: {e}"
    else:
        try:
            agent_reply = agent.run(user_input)

            if vectordb:
                doc_answer = ask_doc_question(vectordb, user_input)
                bot_reply = f"{agent_reply}\n\n📄 From Docs:\n{doc_answer}"
            else:
                bot_reply = agent_reply
        except Exception as e:
            bot_reply = f"❌ Agent error: {e}"

    st.session_state.chat_history.append(("bot", bot_reply))

# --- WhatsApp-style Chat Display ---
for role, msg in st.session_state.chat_history:
    with st.chat_message(role):
        if role == "user":
            st.markdown(f"🧑‍💬 **You**: {msg}")
        else:
            st.markdown(f"🤖 **Bot**: {msg}")

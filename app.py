# app.py

import streamlit as st
from dotenv import load_dotenv
import os
import tempfile
import requests
from openai import OpenAI
from rag import load_and_index_pdf, ask_doc_question
from agent import agent

# --- Load env vars ---
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

# --- Streamlit Config ---
st.set_page_config(page_title="AI Support Bot", layout="centered")
st.title("🤖 AI Customer Support Assistant")

with st.expander("ℹ️ About this Bot", expanded=False):
    st.markdown("""
    This AI assistant supports customers with:
    - 🤖 GPT-powered multi-turn conversations  
    - 📄 PDF knowledge retrieval (RAG)  
    - 👨‍💼 Slack-based human escalation  
    - 📡 Airtable CRM data access  
    """)

# --- PDF Upload Section ---
st.markdown("### 📄 Upload Internal Docs")
uploaded_file = st.file_uploader("Upload product manual, FAQ, or guide (PDF)", type="pdf")

vectordb = None
if uploaded_file:
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name
        vectordb = load_and_index_pdf(tmp_path)
        st.success("✅ Document indexed for Q&A!")
    except Exception as e:
        st.error(f"❌ Could not process PDF: {e}")

# --- Chat Section ---
st.markdown("---")
st.markdown("### 💬 Chat with the Bot")

# State management
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "awaiting_user_info" not in st.session_state:
    st.session_state.awaiting_user_info = False

if "escalation_message" not in st.session_state:
    st.session_state.escalation_message = None

# --- Message Handling ---
with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_input("You:", key="user_input")
    submitted = st.form_submit_button("Send")

# Escalation keywords
escalation_keywords = ["refund", "cancel", "speak to human", "human", "agent", "talk to agent"]

# --- Process User Input ---
if submitted and user_input:
    st.session_state.chat_history.append(("User", user_input))

    # If we're waiting for name/email
    if st.session_state.awaiting_user_info:
        try:
            name, email = user_input.split(",")
            name, email = name.strip(), email.strip()

            slack_message = {
                "text": (
                    f"🚨 Escalation Triggered\n"
                    f"🧑 Name: *{name}*\n"
                    f"📧 Email: *{email}*\n"
                    f"💬 Message: {st.session_state.escalation_message}"
                )
            }
            requests.post(SLACK_WEBHOOK_URL, json=slack_message)
            bot_reply = "✅ Thank you! A human agent has been notified and will reach out shortly."

            st.session_state.awaiting_user_info = False
            st.session_state.escalation_message = None

        except ValueError:
            bot_reply = "⚠️ Please enter both name and email separated by a comma. Example: `Jane Doe, janedoe@email.com`"

    elif any(k in user_input.lower() for k in escalation_keywords):
        st.session_state.awaiting_user_info = True
        st.session_state.escalation_message = user_input
        bot_reply = (
            "🔔 Escalation detected.\n"
            "Please provide your **name and email** so we can notify a human support agent.\n\n"
            "Example: `Jane Doe, janedoe@email.com`"
        )

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

    st.session_state.chat_history.append(("Bot", bot_reply))

# --- Display Chat ---
for role, text in st.session_state.chat_history:
    with st.chat_message(role.lower() if role.lower() == "user" else "assistant"):
        st.markdown(text)

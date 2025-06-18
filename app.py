# app.py
import streamlit as st
import os
import tempfile
from dotenv import load_dotenv
from openai import OpenAI
from rag import load_and_index_pdf, ask_doc_question
from agent import agent
from slack_sdk.webhook import WebhookClient

# Load env
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK_URL")

st.set_page_config(page_title="AI Support Bot", layout="centered")
st.title("🤖 AI Customer Support Assistant")

# --- SESSION STATE ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "vectordb" not in st.session_state:
    st.session_state.vectordb = None

if "user_info" not in st.session_state:
    st.session_state.user_info = {"name": "", "email": ""}

# --- STEP 1: Collect User Info ---
if not st.session_state.user_info["name"] or not st.session_state.user_info["email"]:
    with st.form("user_info_form"):
        st.subheader("👤 Your Information")
        name = st.text_input("Full Name")
        email = st.text_input("Email Address")
        submitted = st.form_submit_button("Start Chat")
        if submitted and name and email:
            st.session_state.user_info["name"] = name
            st.session_state.user_info["email"] = email
            st.success("✅ You can now start chatting!")

    st.stop()

# --- Upload PDF ---
with st.expander("📄 Upload Support Docs (PDF)", expanded=False):
    uploaded_file = st.file_uploader("Upload internal documentation (PDF)", type="pdf")
    if uploaded_file:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name
            st.session_state.vectordb = load_and_index_pdf(tmp_path)
            st.success("✅ Document indexed!")
        except Exception as e:
            st.error(f"❌ PDF error: {e}")

# --- Display History ---
for role, text in st.session_state.chat_history:
    with st.chat_message("user" if role == "User" else "assistant"):
        st.markdown(text)

# --- Chat Input ---
user_input = st.chat_input("Type your message...")
if user_input:
    st.session_state.chat_history.append(("User", user_input))

    # Escalation keywords
    escalation_keywords = ["refund", "talk to human", "agent", "complain", "real person", "escalate"]
    if any(k in user_input.lower() for k in escalation_keywords):
        alert = (
            f"🚨 *Escalation Triggered!*\n"
            f"*Name:* {st.session_state.user_info['name']}\n"
            f"*Email:* {st.session_state.user_info['email']}\n"
            f"*Message:* {user_input}"
        )
        try:
            webhook = WebhookClient(SLACK_WEBHOOK)
            webhook.send(text=alert)
            bot_reply = "🔔 Escalation triggered. A human support agent has been notified."
        except Exception as e:
            bot_reply = f"Slack error: {str(e)}"
    else:
        try:
            # Prefer RAG if PDF is uploaded
            if st.session_state.vectordb:
                bot_reply = ask_doc_question(st.session_state.vectordb, user_input)
            else:
                # Fallback: Airtable CRM agent
                bot_reply = agent.run(user_input)
        except Exception as e:
            bot_reply = f"❌ GPT error: {e}"

    st.session_state.chat_history.append(("Bot", bot_reply))
    with st.chat_message("assistant"):
        st.markdown(bot_reply)

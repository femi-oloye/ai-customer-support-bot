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
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")  # Add this in your .env

# --- Streamlit UI config ---
st.set_page_config(page_title="AI Support Bot", layout="centered")
st.title("🤖 AI Customer Support Assistant")

with st.expander("ℹ️ About this Bot", expanded=False):
    st.markdown("""
    This AI assistant supports customers with:
    - 🤖 Multi-turn GPT conversations  
    - 📄 PDF Retrieval (RAG)  
    - 👨 Human handoff with Slack alerts  
    - 📡 Airtable CRM data access  
    """)

# --- PDF Upload ---
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

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_input("You:", key="user_input")
    submitted = st.form_submit_button("Send")

# --- Escalation Triggers ---
escalation_keywords = ["refund", "cancel", "speak to human", "human", "agent", "talk to agent"]

if submitted and user_input:
    # Append user input
    st.session_state.chat_history.append(("User", user_input))

    # Check for escalation keywords
    if any(k in user_input.lower() for k in escalation_keywords):
        bot_reply = "🔔 Escalation triggered. A human support agent will contact you shortly."

        # Send to Slack
        try:
            slack_message = {
                "text": f"🚨 Escalation triggered from Streamlit Bot\nMessage: *{user_input}*"
            }
            requests.post(SLACK_WEBHOOK_URL, json=slack_message)
            print("✅ Slack escalation sent.")
        except Exception as e:
            bot_reply += f"\n⚠️ Slack error: {e}"
    else:
        try:
            # Use Airtable-aware Agent
            agent_reply = agent.run(user_input)

            # Use RAG if PDF is uploaded
            if vectordb:
                doc_answer = ask_doc_question(vectordb, user_input)
                bot_reply = f"{agent_reply}\n\n📄 From Docs:\n{doc_answer}"
            else:
                bot_reply = agent_reply
        except Exception as e:
            bot_reply = f"❌ Agent error: {e}"

    # Append bot response
    st.session_state.chat_history.append(("Bot", bot_reply))

# --- Display Chat ---
for role, text in st.session_state.chat_history:
    with st.chat_message(role.lower() if role.lower() == "user" else "assistant"):
        st.markdown(text)

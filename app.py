import streamlit as st
from dotenv import load_dotenv
import os
import tempfile
import requests
from openai import OpenAI

from rag import load_and_index_pdf, ask_doc_question
from agent import agent
from airtable_utils import get_customer_info

# Load env variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

client = OpenAI(api_key=OPENAI_API_KEY)

# Streamlit UI setup
st.set_page_config(page_title="AI Customer Support Assistant", layout="centered")
st.title("🤖 AI Customer Support Assistant")

with st.expander("ℹ️ About this Bot", expanded=False):
    st.markdown("""
    This AI assistant supports customers with:
    - Multi-turn GPT conversations  
    - PDF content retrieval (RAG)  
    - Airtable CRM lookup  
    - Complaint detection and escalation to Slack  
    """)

# Upload PDF and index it
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

# Session state to track chat and user info
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "collected_name" not in st.session_state:
    st.session_state.collected_name = None

if "collected_email" not in st.session_state:
    st.session_state.collected_email = None

if "awaiting_name" not in st.session_state:
    st.session_state.awaiting_name = False

if "awaiting_email" not in st.session_state:
    st.session_state.awaiting_email = False

if "escalation_triggered" not in st.session_state:
    st.session_state.escalation_triggered = False

# Chat UI and input
st.markdown("---")
st.markdown("### 💬 Chat with the Bot")

def send_slack_notification(name, email, message):
    try:
        slack_message = {
            "text": (
                f"🚨 *Escalation Alert from AI Support Bot*\n"
                f"*Name:* {name}\n"
                f"*Email:* {email}\n"
                f"*Message:* {message}"
            )
        }
        response = requests.post(SLACK_WEBHOOK_URL, json=slack_message)
        response.raise_for_status()
        print("✅ Slack notification sent.")
    except Exception as e:
        print(f"❌ Slack notification failed: {e}")

with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_input("You:", key="user_input")
    submitted = st.form_submit_button("Send")

if submitted and user_input:

    st.session_state.chat_history.append(("User", user_input))

    # If waiting for name
    if st.session_state.awaiting_name:
        st.session_state.collected_name = user_input.strip()
        st.session_state.awaiting_name = False
        st.session_state.awaiting_email = True
        bot_reply = "Thanks! Now please provide your email address."
        st.session_state.chat_history.append(("Bot", bot_reply))

    # If waiting for email
    elif st.session_state.awaiting_email:
        st.session_state.collected_email = user_input.strip()
        st.session_state.awaiting_email = False

        # Check Airtable for user registration
        customer_info = get_customer_info(st.session_state.collected_email)
        if "No matching customer" in customer_info:
            # Not registered
            bot_reply = (
                f"Hi {st.session_state.collected_name}, it seems you are not registered yet. "
                "You can register at: https://your-registration-link.com"
            )
        else:
            # Registered - provide info
            bot_reply = f"Welcome back {st.session_state.collected_name}! Here is your account info:\n\n{customer_info}"

        st.session_state.chat_history.append(("Bot", bot_reply))

    else:
        # Not awaiting name/email: Normal message processing

        # Check if message is a complaint keyword
        complaint_keywords = ["refund", "cancel", "complaint", "problem", "issue", "not working", "broken"]

        escalation_keywords = ["refund", "cancel", "speak to human", "human", "agent", "talk to agent"]

        message_lower = user_input.lower()

        # If escalation keywords present and user info not collected, ask for name/email first
        if any(k in message_lower for k in escalation_keywords):
            if not st.session_state.collected_name:
                st.session_state.awaiting_name = True
                bot_reply = "I understand you want to talk to a human. Before that, please provide your full name."
                st.session_state.chat_history.append(("Bot", bot_reply))
            elif not st.session_state.collected_email:
                st.session_state.awaiting_email = True
                bot_reply = "Please provide your email address."
                st.session_state.chat_history.append(("Bot", bot_reply))
            else:
                # Escalate to Slack with info
                send_slack_notification(st.session_state.collected_name, st.session_state.collected_email, user_input)
                bot_reply = "🔔 Escalation triggered. A human support agent will contact you shortly."
                st.session_state.chat_history.append(("Bot", bot_reply))

        # If complaint keywords detected AND PDF loaded, use RAG to find solution
        elif any(k in message_lower for k in complaint_keywords) and vectordb:
            try:
                answer = ask_doc_question(vectordb, user_input)
                if answer:
                    bot_reply = f"Based on our documents, here is a possible solution:\n\n{answer}"
                else:
                    bot_reply = "I could not find a solution in the documents. Would you like me to connect you to a human agent?"
            except Exception as e:
                bot_reply = f"❌ Error retrieving document answer: {e}"

            st.session_state.chat_history.append(("Bot", bot_reply))

        else:
            # Normal query: Use agent with Airtable and fallback
            try:
                agent_reply = agent.run(user_input)
                # Add PDF doc answer if available
                if vectordb:
                    doc_answer = ask_doc_question(vectordb, user_input)
                    bot_reply = f"{agent_reply}\n\n📄 From Docs:\n{doc_answer}"
                else:
                    bot_reply = agent_reply
            except Exception as e:
                bot_reply = f"❌ Agent error: {e}"

            st.session_state.chat_history.append(("Bot", bot_reply))

# Display chat history in WhatsApp style
for role, message in st.session_state.chat_history:
    with st.chat_message("user" if role.lower() == "user" else "assistant"):
        st.markdown(message)

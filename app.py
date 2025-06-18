# app.py

import streamlit as st
from dotenv import load_dotenv
import os
import tempfile
from openai import OpenAI
from rag import load_and_index_pdf, ask_doc_question
from agent import agent

# Load environment variables
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Streamlit UI ---
st.set_page_config(page_title="AI Support Bot", layout="centered")
st.title("🤖 AI Customer Support Assistant")

with st.expander("ℹ️ About this Bot", expanded=False):
    st.markdown("""
    This AI-powered assistant handles customer support queries using:
    - 🔁 Multi-turn GPT conversations  
    - 📄 Internal document (PDF) retrieval (RAG)  
    - 📬 Airtable CRM integration  
    - 🧑‍💼 Human escalation handoff  
    """)

# --- Upload PDF ---
st.markdown("### 📄 Upload Internal Docs")
uploaded_file = st.file_uploader("Upload a product manual, FAQ, or internal guide (PDF)", type="pdf")

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

# --- Chat History Setup ---
st.markdown("---")
st.markdown("### 💬 Chat with the Support Bot")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Form Input ---
with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_input("You:", key="user_input")
    submitted = st.form_submit_button("Send")

# --- Email Detection Helper ---
def contains_email(text: str) -> bool:
    import re
    return bool(re.search(r"[\w\.-]+@[\w\.-]+", text))

# --- Response Routing ---
if submitted and user_input:
    st.session_state.chat_history.append(("User", user_input))

    try:
        if contains_email(user_input):
            print("🔍 Routed to: Airtable Agent")
            response = agent.run(user_input)

        elif vectordb:
            print("📄 Routed to: PDF RAG")
            response = ask_doc_question(vectordb, user_input)

        else:
            print("🤖 Routed to: GPT Fallback")
            messages = [{"role": "system", "content": "You are a helpful AI assistant."}]
            for role, msg in st.session_state.chat_history:
                messages.append({"role": "user" if role == "User" else "assistant", "content": msg})
            res = client.chat.completions.create(model="gpt-4", messages=messages)
            response = res.choices[0].message.content.strip()

    except Exception as e:
        response = f"❌ Error: {e}"

    st.session_state.chat_history.append(("Bot", response))

# --- Display Conversation ---
for role, msg in st.session_state.chat_history:
    with st.chat_message(role.lower() if role.lower() == "user" else "assistant"):
        st.markdown(msg)

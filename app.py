# app.py

import streamlit as st
from dotenv import load_dotenv
import os
import tempfile
from openai import OpenAI
from rag import load_and_index_pdf, ask_doc_question
from agent import agent

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(page_title="AI Support Bot", layout="centered")
st.title("🤖 AI Customer Support Assistant")

# Upload Section
st.markdown("### 📄 Upload PDF Knowledge Base")
uploaded_file = st.file_uploader("Upload PDF", type="pdf")

vectordb = None
if uploaded_file:
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name
        vectordb = load_and_index_pdf(tmp_path)
        st.success("✅ Document indexed for Q&A")
    except Exception as e:
        st.error(f"❌ Failed to process PDF: {e}")

# Chat
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.markdown("### 💬 Chat")
with st.form(key="chat_form", clear_on_submit=True):
    user_input = st.text_input("You:", key="user_input")
    submitted = st.form_submit_button("Send")

if submitted and user_input:
    # Try Airtable Agent first
    try:
        response = agent.run(user_input)
    except Exception as e:
        response = f"❌ Agent error: {str(e)}"

    # If fallback to RAG
    if vectordb:
        try:
            response += "\n\n" + ask_doc_question(vectordb, user_input)
        except Exception as e:
            response += f"\n❌ RAG error: {e}"

    st.session_state.chat_history.append(("User", user_input))
    st.session_state.chat_history.append(("Bot", response))

for role, text in st.session_state.chat_history:
    with st.chat_message("user" if role == "User" else "assistant"):
        st.markdown(text)

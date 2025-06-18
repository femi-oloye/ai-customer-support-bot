# app.py
import streamlit as st
from dotenv import load_dotenv
import os
import tempfile
import re
from openai import OpenAI
from rag import load_and_index_pdf, ask_doc_question
from agent import agent

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(page_title="AI Support Bot", layout="centered")
st.title("🤖 AI Customer Support Assistant")

with st.expander("ℹ️ About", expanded=False):
    st.markdown("""
    - ✅ Multi-turn chat
    - 🔍 PDF Question Answering
    - 🧠 CRM query from Airtable
    - 📞 Human handoff detection
    """)

# Upload PDF
st.markdown("### 📄 Upload Internal Docs")
uploaded_file = st.file_uploader("Upload support manual or guide (PDF)", type="pdf")

vectordb = None
if uploaded_file:
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name
        vectordb = load_and_index_pdf(tmp_path)
        st.success("✅ PDF indexed for QA")
    except Exception as e:
        st.error(f"❌ PDF load error: {e}")

# Session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Detects if input is an email question
def contains_email(text):
    return bool(re.search(r"\b[\w.-]+@[\w.-]+\.\w{2,4}\b", text))

# Detects PDF style question
def is_pdf_question(text):
    keywords = ["document", "manual", "guide", "how to", "based on", "policy", "according to"]
    return any(k in text.lower() for k in keywords)

# Chat UI
st.markdown("### 💬 Ask your question")

with st.form("chat_form", clear_on_submit=True):
    user_input = st.text_input("You:", key="user_input")
    submitted = st.form_submit_button("Send")

if submitted and user_input:
    st.session_state.chat_history.append(("User", user_input))

    try:
        if contains_email(user_input):
            print("🔍 Routed to: Airtable Agent")
            response = agent.run(user_input)
        elif vectordb and is_pdf_question(user_input):
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

# Display history
for role, msg in st.session_state.chat_history:
    with st.chat_message(role if role.lower() == "user" else "assistant"):
        st.markdown(msg)

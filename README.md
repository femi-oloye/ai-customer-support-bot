# 🤖 AI-Powered Customer Support Assistant

An intelligent customer support chatbot powered by **GPT-4**, **LangChain**, **RAG**, and **Airtable CRM**.

Supports:
- 💬 Multi-turn chat with context memory
- 📄 Internal document question answering (PDF-based RAG)
- 🧠 GPT-powered fallback
- 🧑‍💼 Escalation to human agents
- 🔗 CRM lookup via Airtable integration

---

## 🚀 Features

| Feature                   | Description                                                  |
|--------------------------|--------------------------------------------------------------|
| ✅ Multi-turn Chat        | Retains conversation context like a real support agent       |
| 📄 RAG PDF Q&A            | Upload internal docs (FAQs, manuals) for doc-based support   |
| 🔍 CRM Lookup             | Pull customer info from Airtable using email addresses       |
| 🧠 GPT-4 Fallback         | Responds to open-ended questions with GPT-4                  |
| 🔔 Escalation Trigger     | Detects keywords like "talk to human" and flags for handoff  |

---

## 🛠️ Tech Stack

- [Streamlit](https://streamlit.io/)
- [LangChain](https://python.langchain.com/)
- [OpenAI GPT-4](https://platform.openai.com/)
- [FAISS](https://github.com/facebookresearch/faiss)
- [Airtable](https://airtable.com/)
- [PyPDF](https://pypdf.readthedocs.io/)

---

## ⚙️ Setup Instructions

### 🔐 1. Environment Variables

Create a `.env` file in the root directory:

```env
OPENAI_API_KEY=your_openai_key
AIRTABLE_API_KEY=your_airtable_key
AIRTABLE_BASE_ID=your_airtable_base_id
```
Example Prompt
“What plan is ibra0oio@gmail.com on?”
→ “The user with the email ibra0oio@gmail.com is on the free plan.”

“Explain refund policy from the uploaded PDF.”

## Use Cases
    SaaS Customer Support

    eCommerce Helpdesk

    Real Estate Chat Assistants

    Internal Company Knowledge Bot


## 👨‍💻 Author
Femi Oloye – AI Automation Engineer
Reach out on Fiverr, Upwork, or LinkedIn
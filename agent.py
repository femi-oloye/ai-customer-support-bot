# agent.py
from langchain.chat_models import ChatOpenAI
from langchain.agents import initialize_agent
from tools import airtable_tool

llm = ChatOpenAI(model_name="gpt-4")

agent = initialize_agent(
    tools=[airtable_tool],
    llm=llm,
    agent_type="openai-tools",
    verbose=True
)

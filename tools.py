# tools.py
from langchain.agents import Tool
from airtable_utils import get_customer_info

airtable_tool = Tool.from_function(
    name="get_customer_info",
    description="Fetch customer support details from Airtable using email address",
    func=get_customer_info
)

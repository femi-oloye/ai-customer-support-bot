# airtable_utils.py
from pyairtable import Table
import os
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE_NAME = "Customers"

table = Table(AIRTABLE_API_KEY, BASE_ID, TABLE_NAME)

def get_customer_info(email: str) -> str:
    records = table.all()
    for record in records:
        fields = record.get("fields", {})
        if fields.get("Email", "").lower() == email.lower():
            name = fields.get("Name", "Unknown")
            plan = fields.get("SubscriptionPlan", "Unknown")
            last_order = fields.get("LastOrderStatus", "Unknown")
            tickets = fields.get("SupportTickets", 0)
            return (
                f"Customer: {name}\n"
                f"Plan: {plan}\n"
                f"Last Order: {last_order}\n"
                f"Open Tickets: {tickets}"
            )
    return "No matching customer found."

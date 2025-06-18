# airtable_utils.py

import os
from dotenv import load_dotenv
from pyairtable import Table
import logging

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE_NAME = "Customers"

if not all([AIRTABLE_API_KEY, BASE_ID]):
    raise ValueError("❌ Missing Airtable credentials in .env")

table = Table(AIRTABLE_API_KEY, BASE_ID, TABLE_NAME)

def get_customer_info(email: str) -> str:
    try:
        records = table.all()
    except Exception as e:
        logging.error(f"❌ Airtable API error: {e}")
        return f"❌ Airtable error: {str(e)}"

    for record in records:
        fields = record.get('fields', {})
        if fields.get('Email', '').lower() == email.lower():
            return (
                f"Name: {fields.get('Name', 'N/A')}\n"
                f"Plan: {fields.get('SubscriptionPlan', 'Unknown')}\n"
                f"Last Order: {fields.get('LastOrderStatus', 'Unknown')}\n"
                f"Open Tickets: {fields.get('SupportTickets', 0)}"
            )
    return "❌ No matching customer found."

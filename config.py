import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DATABASE_NAME = "budget_tracker"
EXPENSES_COLLECTION = "expenses"
INVESTMENTS_COLLECTION = "investments"
MISCELLANEOUS_COLLECTION = "miscellaneous"

CURRENCY_SYMBOL = "₹"

CATEGORIES = [
    "Food",
    "Transport",
    "Rent",
    "Shopping",
    "Bills",
    "Other",
]

INVESTMENT_CATEGORIES = [
    "Mutual Fund",
    "SIP",
    "Stocks",
    "PPF",
    "NPS",
    "Gold",
    "Fixed Deposit",
    "Other Investment",
]

MISCELLANEOUS_CATEGORIES = [
    "Home",
    "Factory",
    "Bills",
    "Gifts",
    "Repairs",
    "Other",
]

INVESTMENT_CHART_COLORS = {
    "Mutual Fund": "#6C5CE7",
    "SIP": "#A29BFE",
    "Stocks": "#00B894",
    "PPF": "#00CEC9",
    "NPS": "#FDCB6E",
    "Gold": "#E17055",
    "Fixed Deposit": "#74B9FF",
    "Other Investment": "#B2BEC3",
}

CHART_COLORS = {
    "Food": "#FF6B6B",
    "Transport": "#4ECDC4",
    "Rent": "#45B7D1",
    "Shopping": "#FFA07A",
    "Bills": "#98D8C8",
    "Other": "#C7CEEA",
}

PAGE_TITLE = "Expense Tracker"
PAGE_ICON = "📊"
LAYOUT = "wide"

import streamlit as st
from datetime import datetime
import config
from database.models import ExpenseModel
from database.category_model import CategoryModel
from utils.validators import validate_amount, validate_date, validate_description, validate_category


def render_expense_form():
    if "expense_added" not in st.session_state:
        st.session_state.expense_added = False

    with st.form("expense_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            expense_date = st.date_input(
                "📅 Date",
                value=datetime.now(),
                max_value=datetime.now(),
                help="Select the date of the expense",
            )
        with col2:
            all_categories = CategoryModel.get_all_categories()
            category = st.selectbox(
                "🏷️ Category",
                options=all_categories,
                help="Select expense category",
            )

        description = st.text_input(
            "📝 Description (Optional)",
            placeholder="e.g., Grocery shopping at supermarket",
        )
        amount = st.number_input(
            f"💰 Amount ({config.CURRENCY_SYMBOL})",
            min_value=0.0,
            value=None,
            step=10.0,
            format="%.2f",
            placeholder="0.0",
        )
        st.divider()
        submitted = st.form_submit_button("💾 Add Expense", width='stretch', type="primary")

        if submitted:
            errors = []
            expense_datetime = datetime.combine(expense_date, datetime.min.time())

            for ok, msg in [
                validate_date(expense_datetime),
                validate_category(category, all_categories),
                validate_description(description),
                validate_amount(amount),
            ]:
                if not ok:
                    errors.append(msg)

            if errors:
                for error in errors:
                    st.error(error)
            else:
                success = ExpenseModel.create_expense(
                    date=expense_datetime,
                    category=category,
                    description=description,
                    amount=amount,
                )
                if success:
                    st.session_state.expense_added = True
                    st.session_state.expense_added_amount = amount
                else:
                    st.error("❌ Failed to add expense. Please try again.")

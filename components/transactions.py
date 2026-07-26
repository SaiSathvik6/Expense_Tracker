import streamlit as st
import config
from datetime import datetime
from components.expense_form import render_expense_form
from database.models import ExpenseModel
from database.category_model import CategoryModel
from utils.helpers import get_month_name, get_month_start_end


def render_transactions():
    st.header("💳 Transactions")
    st.divider()
    st.subheader("Add New Expense")
    render_expense_form()

    if st.session_state.get("expense_added"):
        amount = st.session_state.get("expense_added_amount", 0)
        st.success(f"✅ Expense of {config.CURRENCY_SYMBOL}{amount:,.2f} added successfully!")
        st.balloons()
        st.session_state.expense_added = False
        st.session_state.expense_added_amount = 0
        st.rerun()

    st.divider()
    st.subheader("📜 Expense History")

    col1, col2, col3 = st.columns(3)

    available_years = ExpenseModel.get_available_years()
    available_year_months = ExpenseModel.get_available_year_months()
    current_year = datetime.now().year
    current_month = datetime.now().month

    with col1:
        if current_year not in available_years:
            available_years.insert(0, current_year)
        selected_year = st.selectbox(
            "📅 Year",
            options=available_years,
            index=0,
            key="trans_year_select",
        )

    with col2:
        available_months = sorted([ym[1] for ym in available_year_months if ym[0] == selected_year])
        if selected_year == current_year and current_month not in available_months:
            available_months = sorted(available_months + [current_month], reverse=True)

        if available_months:
            default_index = 0
            if selected_year == current_year:
                try:
                    default_index = available_months.index(current_month)
                except ValueError:
                    default_index = 0
            selected_month = st.selectbox(
                "📅 Month",
                options=available_months,
                format_func=get_month_name,
                index=default_index,
                key="trans_month_select",
            )
        else:
            selected_month = current_month
            st.info(f"No data for {selected_year}.")

    with col3:
        all_categories = CategoryModel.get_all_categories()
        selected_category = st.selectbox(
            "🏷️ Category",
            options=["All Categories"] + all_categories,
            index=0,
            key="trans_category_select",
        )

    start_date, end_date = get_month_start_end(selected_year, selected_month)
    filter_label = f"{get_month_name(selected_month)} {selected_year}"
    render_expense_history(start_date, end_date, filter_label, selected_category)


def render_expense_history(start_date, end_date, filter_label, selected_category="All Categories"):
    expenses = ExpenseModel.get_expenses(start_date, end_date) if (start_date and end_date) else ExpenseModel.get_expenses()

    if selected_category != "All Categories":
        expenses = [e for e in expenses if e.get("category") == selected_category]

    if not expenses:
        label = f"**{selected_category}** in {filter_label}" if selected_category != "All Categories" else filter_label
        st.info(f"No expenses recorded for {label}.")
        return

    currency = config.CURRENCY_SYMBOL
    total_amount = sum(e["amount"] for e in expenses)

    st.markdown("""
    <style>
    button[data-testid="stBaseButton-secondary"] {
        background: none !important;
        border: none !important;
        box-shadow: none !important;
        padding: 2px 6px !important;
        min-height: unset !important;
        height: auto !important;
        font-size: 1rem !important;
        line-height: 1 !important;
    }
    button[data-testid="stBaseButton-secondary"]:hover {
        background: rgba(255,255,255,0.08) !important;
        border-radius: 4px !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Header
    h1, h2, h3, h4, h5 = st.columns([2, 2, 4, 2, 1])
    headers = [(h1, "Date", "left"), (h2, "Category", "left"),
               (h3, "Description", "left"), (h4, "Amount", "right"), (h5, "Action", "center")]
    for col, label, align in headers:
        with col:
            st.markdown(
                f"<div style='color:#888;font-size:0.72rem;font-weight:700;"
                f"text-transform:uppercase;letter-spacing:0.06em;"
                f"padding:4px 0 8px;border-bottom:2px solid #333;"
                f"text-align:{align}'>{label}</div>",
                unsafe_allow_html=True,
            )

    # Scrollable rows
    with st.container(height=400):
        cell = "padding:9px 0;border-bottom:1px solid #1f1f1f;font-size:0.875rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;"
        for i, exp in enumerate(expenses):
            date_str = exp["date"].strftime("%d %b %Y") if hasattr(exp["date"], "strftime") else str(exp["date"])
            desc     = exp.get("description") or "—"
            category = exp.get("category", "—")
            amount   = exp["amount"]
            exp_id   = str(exp["_id"])

            c1, c2, c3, c4, c5 = st.columns([2, 2, 4, 2, 1])
            with c1:
                st.markdown(f"<div style='{cell}color:#999'>{date_str}</div>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"<div style='{cell}'>{category}</div>", unsafe_allow_html=True)
            with c3:
                st.markdown(f"<div style='{cell}color:#bbb'>{desc}</div>", unsafe_allow_html=True)
            with c4:
                st.markdown(f"<div style='{cell}color:#ff6b35;font-weight:600;text-align:right'>{currency}{amount:,.2f}</div>", unsafe_allow_html=True)
            with c5:
                b1, b2 = st.columns(2)
                with b1:
                    if st.button("✏️", key=f"edit_{exp_id}_{i}", help="Edit"):
                        st.session_state.editing_expense = exp
                        st.rerun()
                with b2:
                    if st.button("🗑️", key=f"del_{exp_id}_{i}", help="Delete"):
                        if ExpenseModel.delete_expense(exp_id):
                            st.success("Expense deleted.")
                            st.rerun()
                        else:
                            st.error("Failed to delete expense.")

    # Total bar
    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;
        padding:8px 2px;margin-top:4px;border-top:1px solid #2a2a2a;">
      <span style="color:#666;font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;">
        {len(expenses)} expense(s)
      </span>
      <span style="color:#ff6b35;font-weight:700;font-size:1rem;">
        Total &nbsp;{currency}{total_amount:,.2f}
      </span>
    </div>
    """, unsafe_allow_html=True)

    if "editing_expense" in st.session_state:
        render_edit_form(st.session_state.editing_expense)


def render_edit_form(expense):
    st.divider()
    st.subheader("✏️ Edit Expense")

    with st.form("edit_expense_form"):
        col1, col2 = st.columns(2)
        with col1:
            new_date = st.date_input("Date", value=expense["date"], max_value=datetime.now())
        with col2:
            all_categories = CategoryModel.get_all_categories()
            try:
                cat_index = all_categories.index(expense["category"])
            except ValueError:
                cat_index = 0
            new_category = st.selectbox("Category", options=all_categories, index=cat_index)

        new_description = st.text_input("Description", value=expense["description"])
        new_amount = st.number_input(
            f"Amount ({config.CURRENCY_SYMBOL})",
            value=float(expense["amount"]),
            min_value=0.0,
            step=10.0,
            format="%.2f",
        )

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("💾 Save Changes", width='stretch')
        with col2:
            cancelled = st.form_submit_button("❌ Cancel", width='stretch')

        if submitted:
            if ExpenseModel.update_expense(
                str(expense["_id"]),
                datetime.combine(new_date, datetime.min.time()),
                new_category,
                new_description,
                new_amount,
            ):
                st.success("Expense updated successfully!")
                del st.session_state.editing_expense
                st.rerun()
            else:
                st.error("Failed to update expense.")

        if cancelled:
            del st.session_state.editing_expense
            st.rerun()
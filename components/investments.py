import streamlit as st
import config
from datetime import datetime
from database.investment_model import InvestmentModel
from database.investment_category_model import InvestmentCategoryModel
from utils.helpers import get_month_name, get_month_start_end


def render_investments():
    st.header("📈 Investments")
    st.divider()
    st.subheader("Add New Investment")
    render_investment_form()

    if st.session_state.get("investment_added"):
        amount = st.session_state.get("investment_added_amount", 0)
        st.success(f"✅ Investment of {config.CURRENCY_SYMBOL}{amount:,.2f} added successfully!")
        st.balloons()
        st.session_state.investment_added = False
        st.session_state.investment_added_amount = 0
        st.rerun()

    st.divider()
    st.subheader("📜 Investment History")

    col1, col2, col3 = st.columns(3)

    available_years = InvestmentModel.get_available_years()
    available_year_months = InvestmentModel.get_available_year_months()
    current_year = datetime.now().year
    current_month = datetime.now().month

    with col1:
        if current_year not in available_years:
            available_years.insert(0, current_year)
        selected_year = st.selectbox(
            "📅 Year",
            options=available_years,
            index=0,
            key="inv_year_select",
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
                key="inv_month_select",
            )
        else:
            selected_month = current_month
            st.info(f"No data for {selected_year}.")

    with col3:
        all_inv_categories = InvestmentCategoryModel.get_all_categories()
        selected_category = st.selectbox(
            "🏷️ Category",
            options=["All Categories"] + all_inv_categories,
            index=0,
            key="inv_category_select",
        )

    start_date, end_date = get_month_start_end(selected_year, selected_month)
    filter_label = f"{get_month_name(selected_month)} {selected_year}"
    render_investment_history(start_date, end_date, filter_label, selected_category)


def render_investment_form():
    if "investment_added" not in st.session_state:
        st.session_state.investment_added = False

    with st.form("investment_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            investment_date = st.date_input(
                "📅 Date",
                value=datetime.now(),
                max_value=datetime.now(),
            )
        with col2:
            category = st.selectbox(
                "🏷️ Category",
                options=InvestmentCategoryModel.get_all_categories(),
            )

        description = st.text_input(
            "📝 Description (Optional)",
            placeholder="e.g., Axis Bluechip Fund SIP",
        )
        amount = st.number_input(
            f"💰 Amount ({config.CURRENCY_SYMBOL})",
            min_value=0.0,
            value=None,
            step=100.0,
            format="%.2f",
            placeholder="0.0",
        )
        st.divider()
        submitted = st.form_submit_button("💾 Add Investment", width='stretch', type="primary")

        if submitted:
            errors = []
            if amount is None or amount <= 0:
                errors.append("Amount must be greater than zero.")
            if errors:
                for error in errors:
                    st.error(error)
            else:
                investment_datetime = datetime.combine(investment_date, datetime.min.time())
                success = InvestmentModel.create_investment(
                    date=investment_datetime,
                    category=category,
                    description=description,
                    amount=amount,
                )
                if success:
                    st.session_state.investment_added = True
                    st.session_state.investment_added_amount = amount
                else:
                    st.error("❌ Failed to add investment. Please try again.")


def render_investment_history(start_date, end_date, filter_label, selected_category="All Categories"):
    investments = InvestmentModel.get_investments(start_date, end_date) if (start_date and end_date) else InvestmentModel.get_investments()

    if selected_category != "All Categories":
        investments = [i for i in investments if i.get("category") == selected_category]

    if not investments:
        label = f"**{selected_category}** in {filter_label}" if selected_category != "All Categories" else filter_label
        st.info(f"No investments recorded for {label}.")
        return

    currency = config.CURRENCY_SYMBOL
    total_amount = sum(i["amount"] for i in investments)

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

    with st.container(height=400):
        cell = "padding:9px 0;border-bottom:1px solid #1f1f1f;font-size:0.875rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;"
        for idx, inv in enumerate(investments):
            date_str = inv["date"].strftime("%d %b %Y") if hasattr(inv["date"], "strftime") else str(inv["date"])
            desc     = inv.get("description") or "—"
            category = inv.get("category", "—")
            amount   = inv["amount"]
            inv_id   = str(inv["_id"])

            c1, c2, c3, c4, c5 = st.columns([2, 2, 4, 2, 1])
            with c1:
                st.markdown(f"<div style='{cell}color:#999'>{date_str}</div>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"<div style='{cell}'>{category}</div>", unsafe_allow_html=True)
            with c3:
                st.markdown(f"<div style='{cell}color:#bbb'>{desc}</div>", unsafe_allow_html=True)
            with c4:
                st.markdown(f"<div style='{cell}color:#6C5CE7;font-weight:600;text-align:right'>{currency}{amount:,.2f}</div>", unsafe_allow_html=True)
            with c5:
                b1, b2 = st.columns(2)
                with b1:
                    if st.button("✏️", key=f"inv_edit_{inv_id}_{idx}", help="Edit"):
                        st.session_state.editing_investment = inv
                        st.rerun()
                with b2:
                    if st.button("🗑️", key=f"inv_del_{inv_id}_{idx}", help="Delete"):
                        if InvestmentModel.delete_investment(inv_id):
                            st.success("Investment deleted.")
                            st.rerun()
                        else:
                            st.error("Failed to delete investment.")

    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;
        padding:8px 2px;margin-top:4px;border-top:1px solid #2a2a2a;">
      <span style="color:#666;font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;">
        {len(investments)} investment(s)
      </span>
      <span style="color:#6C5CE7;font-weight:700;font-size:1rem;">
        Total &nbsp;{currency}{total_amount:,.2f}
      </span>
    </div>
    """, unsafe_allow_html=True)

    if "editing_investment" in st.session_state:
        render_edit_form(st.session_state.editing_investment)


def render_edit_form(investment):
    st.divider()
    st.subheader("✏️ Edit Investment")

    with st.form("edit_investment_form"):
        col1, col2 = st.columns(2)
        with col1:
            new_date = st.date_input("Date", value=investment["date"], max_value=datetime.now())
        with col2:
            all_inv_cats = InvestmentCategoryModel.get_all_categories()
            try:
                cat_index = all_inv_cats.index(investment["category"])
            except ValueError:
                cat_index = 0
            new_category = st.selectbox("Category", options=all_inv_cats, index=cat_index)

        new_description = st.text_input("Description", value=investment.get("description", ""))
        new_amount = st.number_input(
            f"Amount ({config.CURRENCY_SYMBOL})",
            value=float(investment["amount"]),
            min_value=0.0,
            step=100.0,
            format="%.2f",
        )

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("💾 Save Changes", width='stretch')
        with col2:
            cancelled = st.form_submit_button("❌ Cancel", width='stretch')

        if submitted:
            if InvestmentModel.update_investment(
                str(investment["_id"]),
                datetime.combine(new_date, datetime.min.time()),
                new_category,
                new_description,
                new_amount,
            ):
                st.success("Investment updated successfully!")
                del st.session_state.editing_investment
                st.rerun()
            else:
                st.error("Failed to update investment.")

        if cancelled:
            del st.session_state.editing_investment
            st.rerun()

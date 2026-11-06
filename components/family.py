import streamlit as st
import pandas as pd
import plotly.express as px
import config
from datetime import datetime
from database.miscellaneous_model import MiscellaneousModel
from utils.helpers import format_currency, get_month_name, get_month_start_end

MISC_COLOR = "#F7B731"


def render_family():
    st.header("👨‍👩‍👧 Family")
    st.markdown(
        "Track family spends like **home** purchases, bills, gifts and repairs "
        "separately from your day-to-day expenses."
    )

    if st.session_state.get("misc_added"):
        amount = st.session_state.get("misc_added_amount", 0)
        st.success(f"✅ Entry of {config.CURRENCY_SYMBOL}{amount:,.2f} added successfully!")
        st.session_state.misc_added = False
        st.session_state.misc_added_amount = 0

    # A keyed radio (not st.tabs) so the selected view survives reruns after add/edit/delete
    view = st.radio(
        "View",
        options=["📊 Overview", "➕ Add Entry", "📜 History"],
        horizontal=True,
        key="misc_view",
        label_visibility="collapsed",
    )

    if view == "📊 Overview":
        render_overview()
    elif view == "➕ Add Entry":
        render_misc_form()
    elif view == "📜 History":
        render_history_tab()


def _select_year(key: str) -> int:
    available_years = MiscellaneousModel.get_available_years()
    current_year = datetime.now().year
    if current_year not in available_years:
        available_years.insert(0, current_year)
    return st.selectbox("📅 Year", options=available_years, index=0, key=key)


def _year_range(year: int):
    start_date, _ = get_month_start_end(year, 1)
    _, end_date = get_month_start_end(year, 12)
    return start_date, end_date


def render_overview():
    selected_year = _select_year("misc_overview_year_select")
    year_entries = MiscellaneousModel.get_entries(*_year_range(selected_year))
    yearly_totals = MiscellaneousModel.get_yearly_monthly_totals(selected_year)
    all_time_total = sum(e["amount"] for e in MiscellaneousModel.get_entries())

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(f"🧾 Total {selected_year}", format_currency(sum(e["amount"] for e in year_entries)))
    with col2:
        st.metric(f"📊 Entries {selected_year}", str(len(year_entries)))
    with col3:
        st.metric("🏦 All Time", format_currency(all_time_total))

    st.divider()
    st.subheader(f"Monthly Family Spend ({selected_year})")

    months = [m for m in range(1, 13) if yearly_totals[m] > 0]
    if not months:
        st.info(f"No family entries recorded for {selected_year}.")
        return

    df = pd.DataFrame({
        "month": [get_month_name(m) for m in months],
        "amount": [yearly_totals[m] for m in months],
    })
    fig = px.bar(
        df,
        x="month",
        y="amount",
        labels={"month": "Month", "amount": f"Amount ({config.CURRENCY_SYMBOL})"},
    )
    fig.update_traces(marker_color=MISC_COLOR)
    fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, width='stretch')

    breakdown: dict = {}
    for e in year_entries:
        breakdown[e["category"]] = breakdown.get(e["category"], 0.0) + e["amount"]

    st.subheader(f"Category Summary ({selected_year})")
    summary = pd.DataFrame(
        sorted(breakdown.items(), key=lambda kv: kv[1], reverse=True),
        columns=["category", "amount"],
    )
    summary["amount"] = summary["amount"].apply(format_currency)
    st.dataframe(summary, width='stretch', hide_index=True)


def render_misc_form():
    with st.form("misc_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            entry_date = st.date_input(
                "📅 Date",
                value=datetime.now(),
                max_value=datetime.now(),
            )
        with col2:
            category = st.selectbox(
                "🏷️ Category",
                options=config.MISCELLANEOUS_CATEGORIES,
            )

        description = st.text_input(
            "📝 Description (Optional)",
            placeholder="e.g., CCTV + wiring",
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
        submitted = st.form_submit_button("💾 Add Entry", width='stretch', type="primary")

        if submitted:
            if amount is None or amount <= 0:
                st.error("Amount must be greater than zero.")
            else:
                success = MiscellaneousModel.create_entry(
                    date=datetime.combine(entry_date, datetime.min.time()),
                    category=category,
                    description=description,
                    amount=amount,
                )
                if success:
                    st.session_state.misc_added = True
                    st.session_state.misc_added_amount = amount
                    st.rerun()
                else:
                    st.error("❌ Failed to add entry. Please try again.")


def render_history_tab():
    col1, col2 = st.columns(2)
    with col1:
        selected_year = _select_year("misc_history_year_select")
    with col2:
        selected_category = st.selectbox(
            "🏷️ Category",
            options=["All Categories"] + config.MISCELLANEOUS_CATEGORIES,
            index=0,
            key="misc_category_select",
        )

    start_date, end_date = _year_range(selected_year)
    render_misc_history(start_date, end_date, str(selected_year), selected_category)


def render_misc_history(start_date, end_date, filter_label, selected_category="All Categories"):
    entries = MiscellaneousModel.get_entries(start_date, end_date)

    if selected_category != "All Categories":
        entries = [e for e in entries if e.get("category") == selected_category]

    if not entries:
        label = f"**{selected_category}** in {filter_label}" if selected_category != "All Categories" else filter_label
        st.info(f"No family entries recorded for {label}.")
        return

    currency = config.CURRENCY_SYMBOL
    total_amount = sum(e["amount"] for e in entries)

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
        for idx, entry in enumerate(entries):
            date_str = entry["date"].strftime("%d %b %Y") if hasattr(entry["date"], "strftime") else str(entry["date"])
            desc     = entry.get("description") or "—"
            category = entry.get("category", "—")
            amount   = entry["amount"]
            entry_id = str(entry["_id"])

            c1, c2, c3, c4, c5 = st.columns([2, 2, 4, 2, 1])
            with c1:
                st.markdown(f"<div style='{cell}color:#999'>{date_str}</div>", unsafe_allow_html=True)
            with c2:
                st.markdown(f"<div style='{cell}'>{category}</div>", unsafe_allow_html=True)
            with c3:
                st.markdown(f"<div style='{cell}color:#bbb'>{desc}</div>", unsafe_allow_html=True)
            with c4:
                st.markdown(f"<div style='{cell}color:{MISC_COLOR};font-weight:600;text-align:right'>{currency}{amount:,.2f}</div>", unsafe_allow_html=True)
            with c5:
                b1, b2 = st.columns(2)
                with b1:
                    if st.button("✏️", key=f"misc_edit_{entry_id}_{idx}", help="Edit"):
                        st.session_state.editing_misc = entry
                        st.rerun()
                with b2:
                    if st.button("🗑️", key=f"misc_del_{entry_id}_{idx}", help="Delete"):
                        if MiscellaneousModel.delete_entry(entry_id):
                            st.success("Entry deleted.")
                            st.rerun()
                        else:
                            st.error("Failed to delete entry.")

    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;
        padding:8px 2px;margin-top:4px;border-top:1px solid #2a2a2a;">
      <span style="color:#666;font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.05em;">
        {len(entries)} entr{"y" if len(entries) == 1 else "ies"}
      </span>
      <span style="color:{MISC_COLOR};font-weight:700;font-size:1rem;">
        Total &nbsp;{currency}{total_amount:,.2f}
      </span>
    </div>
    """, unsafe_allow_html=True)

    if "editing_misc" in st.session_state:
        render_edit_form(st.session_state.editing_misc)


def render_edit_form(entry):
    st.divider()
    st.subheader("✏️ Edit Entry")

    with st.form("edit_misc_form"):
        col1, col2 = st.columns(2)
        with col1:
            new_date = st.date_input("Date", value=entry["date"], max_value=datetime.now())
        with col2:
            categories = config.MISCELLANEOUS_CATEGORIES
            try:
                cat_index = categories.index(entry["category"])
            except ValueError:
                cat_index = 0
            new_category = st.selectbox("Category", options=categories, index=cat_index)

        new_description = st.text_input("Description", value=entry.get("description", ""))
        new_amount = st.number_input(
            f"Amount ({config.CURRENCY_SYMBOL})",
            value=float(entry["amount"]),
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
            if MiscellaneousModel.update_entry(
                str(entry["_id"]),
                datetime.combine(new_date, datetime.min.time()),
                new_category,
                new_description,
                new_amount,
            ):
                st.success("Entry updated successfully!")
                del st.session_state.editing_misc
                st.rerun()
            else:
                st.error("Failed to update entry.")

        if cancelled:
            del st.session_state.editing_misc
            st.rerun()

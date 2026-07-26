import calendar
import streamlit as st
from datetime import datetime, date
from database.event_model import EventModel
from database.category_model import CategoryModel
from database.investment_category_model import InvestmentCategoryModel
from utils.helpers import format_currency
import config


def _categories_for_type(event_type: str):
    if event_type == "investment":
        return InvestmentCategoryModel.get_all_categories()
    return CategoryModel.get_all_categories()


def render_payments():
    st.header("🗓️ Recurring Payments")
    st.markdown(
        "Schedule recurring payment entries that are **automatically posted** "
        "daily or on a chosen day every month."
    )
    _auto_run_scheduler()
    # st.divider()

    tab1, tab2, tab3 = st.tabs(["📋 My Payments", "➕ Add Payment", "⚡ Scheduler"])
    with tab1:
        render_event_list()
    with tab2:
        render_add_event_form()
    with tab3:
        render_scheduler_panel()


def _auto_run_scheduler():
    results = EventModel.run_due_events()
    executed = [r for r in results if r["status"] == "executed"]
    if executed:
        names = ", ".join(r["event"]["title"] for r in executed)
        st.success(f"✅ **Auto-executed {len(executed)} payment(s):** {names}")


def render_event_list():
    events = EventModel.get_all_events()
    if not events:
        st.info("No recurring payments yet. Go to **Add Payment** to create one.")
        return

    today = date.today()

    for event in events:
        event_id = str(event["_id"])
        frequency = event.get("frequency", "monthly")
        is_active = event.get("is_active", True)

        if frequency == "daily":
            already_done = EventModel.has_been_executed_today(event_id, today)
            if not is_active:
                badge, border_color = "⏸️ Paused", "#555"
            elif already_done:
                badge, border_color = "✅ Done today", "#2ecc71"
            else:
                badge, border_color = "🔄 Due today", "#f39c12"
            schedule_label = "Every day"
        else:
            day = event["day_of_month"]
            last_day = calendar.monthrange(today.year, today.month)[1]
            effective_day = min(day, last_day)
            due_date = date(today.year, today.month, effective_day)
            already_done = EventModel.has_been_executed(event_id, today.year, today.month)

            if not is_active:
                badge, border_color = "⏸️ Paused", "#555"
            elif already_done:
                badge, border_color = "✅ Done this month", "#2ecc71"
            elif today == due_date:
                badge, border_color = "🔄 Executing today", "#f39c12"
            elif today < due_date:
                badge, border_color = f"⏳ Due on {due_date.strftime('%d %b')} (this month)", "#3498db"
            else:
                if today.month == 12:
                    nd = date(today.year + 1, 1, min(day, 31))
                else:
                    nm_last = calendar.monthrange(today.year, today.month + 1)[1]
                    nd = date(today.year, today.month + 1, min(day, nm_last))
                badge, border_color = f"🔜 Next month ({nd.strftime('%d %b %Y')})", "#9b59b6"
            schedule_label = f"{day}{_ordinal(day)} of every month"

        with st.container():
            st.markdown(
                f"""<div style="border-left: 4px solid {border_color};
                            padding: 0.6rem 1rem; margin-bottom: 0.5rem;
                            border-radius: 6px; background: rgba(255,255,255,0.04);">
                    <span style="font-size:1.05rem; font-weight:600;">{event['title']}</span>
                    &nbsp;&nbsp;
                    <span style="font-size:0.82rem; color:#aaa;">{badge}</span>
                </div>""",
                unsafe_allow_html=True,
            )

            col_info, col_actions = st.columns([3, 1])

            with col_info:
                desc = event.get("description", "") or "—"
                etype = event.get("event_type", "expense")
                etype_label = "📈 Investment" if etype == "investment" else "💸 Expense"
                freq_label = "🔁 Daily" if frequency == "daily" else "📅 Monthly"
                st.markdown(
                    f"**Amount:** {format_currency(event['amount'])}  |  "
                    f"**Type:** {etype_label}  |  "
                    f"**Frequency:** {freq_label}  |  "
                    f"**Category:** {event['category']}  |  "
                    f"**Schedule:** {schedule_label}  |  "
                    f"**Note:** {desc}"
                )
                history = EventModel.get_execution_history(event_id)
                if history:
                    with st.expander(f"📜 Execution history ({len(history)} entries)"):
                        for h in history[:12]:
                            executed_at = h.get("executed_at", "")
                            if isinstance(executed_at, datetime):
                                executed_at = executed_at.strftime("%d %b %Y %H:%M")
                            if frequency == "daily" and h.get("day"):
                                period = f"{h['day']} {calendar.month_abbr[h['month']]} {h['year']}"
                            else:
                                period = f"{calendar.month_abbr[h['month']]} {h['year']}"
                            st.markdown(f"- **{period}** — executed at {executed_at}")

            with col_actions:
                if st.button("🚀 Execute Now", key=f"exec_{event_id}", width='stretch'):
                    if EventModel.execute_single_event(event_id):
                        st.rerun()
                    else:
                        st.error("Failed to execute.")

                toggle_label = "⏸️ Pause" if is_active else "▶️ Resume"
                if st.button(toggle_label, key=f"toggle_{event_id}", width='stretch'):
                    EventModel.toggle_event(event_id, not is_active)
                    st.rerun()

                if st.button("✏️ Edit", key=f"edit_{event_id}", width='stretch'):
                    st.session_state["editing_event"] = event_id
                    st.rerun()

                if st.button("🗑️ Delete", key=f"del_{event_id}", width='stretch'):
                    st.session_state[f"confirm_del_{event_id}"] = True
                    st.rerun()

                if st.session_state.get(f"confirm_del_{event_id}"):
                    st.warning("Are you sure?")
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("Yes", key=f"yes_{event_id}"):
                            EventModel.delete_event(event_id)
                            del st.session_state[f"confirm_del_{event_id}"]
                            st.rerun()
                    with c2:
                        if st.button("No", key=f"no_{event_id}"):
                            del st.session_state[f"confirm_del_{event_id}"]
                            st.rerun()

        if st.session_state.get("editing_event") == event_id:
            _render_edit_form(event)

        st.markdown("---")


def _render_edit_form(event):
    event_id = str(event["_id"])
    current_type = event.get("event_type", "expense")
    current_frequency = event.get("frequency", "monthly")

    freq_key = f"edit_freq_{event_id}"
    if freq_key not in st.session_state:
        st.session_state[freq_key] = current_frequency

    st.markdown("#### ✏️ Edit Payment")

    # Frequency outside the form so changing it immediately hides/shows Day of Month
    st.markdown("#### 🔁 Frequency")
    st.radio(
        "Frequency",
        options=["monthly", "daily"],
        format_func=lambda x: "📅 Monthly" if x == "monthly" else "🔁 Daily",
        key=freq_key,
        horizontal=True,
        label_visibility="collapsed",
    )
    frequency = st.session_state[freq_key]

    with st.form(f"edit_form_{event_id}"):
        event_type = st.radio(
            "Payment Type",
            options=["expense", "investment"],
            format_func=lambda x: "💸 Expense" if x == "expense" else "📈 Investment",
            index=0 if current_type == "expense" else 1,
            horizontal=True,
        )
        categories = _categories_for_type(event_type)

        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("Payment Name", value=event["title"])
            amount = st.number_input(
                f"Amount ({config.CURRENCY_SYMBOL})",
                min_value=0.01,
                value=float(event["amount"]),
                step=0.01,
                format="%.2f",
            )
        with col2:
            cat_idx = categories.index(event["category"]) if event["category"] in categories else 0
            category = st.selectbox("Category", categories, index=cat_idx)
            if frequency == "monthly":
                day_of_month = st.number_input(
                    "Day of Month (1–28)",
                    min_value=1,
                    max_value=28,
                    value=int(event["day_of_month"]),
                )
            else:
                day_of_month = int(event["day_of_month"])

        description = st.text_input("Description / Note", value=event.get("description", ""))
        is_active = st.checkbox("Active", value=event.get("is_active", True))

        c1, c2 = st.columns(2)
        with c1:
            submitted = st.form_submit_button("💾 Save Changes", width='stretch')
        with c2:
            cancelled = st.form_submit_button("✖ Cancel", width='stretch')

    if submitted:
        if not title.strip():
            st.error("Payment name cannot be empty.")
        elif amount <= 0:
            st.error("Amount must be positive.")
        else:
            ok = EventModel.update_event(
                event_id, title, category, amount, day_of_month,
                description, is_active, event_type, frequency,
            )
            if ok:
                st.success("✅ Payment updated!")
                del st.session_state["editing_event"]
                if freq_key in st.session_state:
                    del st.session_state[freq_key]
                st.rerun()
            else:
                st.error("Failed to update payment.")

    if cancelled:
        del st.session_state["editing_event"]
        if freq_key in st.session_state:
            del st.session_state[freq_key]
        st.rerun()


def render_add_event_form():
    # st.subheader("➕ Create Recurring Payment")
    # st.markdown(
    #     "Every payment you create will **automatically generate an expense or investment entry** "
    #     "daily or on the chosen day of each month."
    # )

    # Frequency outside the form so changing it immediately hides/shows Day of Month
    st.markdown("#### 🔁 Frequency")
    frequency = st.radio(
        "Frequency",
        options=["monthly", "daily"],
        format_func=lambda x: "📅 Monthly — runs once per month on a chosen day"
                              if x == "monthly"
                              else "🔁 Daily — runs every day automatically",
        key="add_payment_frequency",
        horizontal=True,
        label_visibility="collapsed",
    )

    with st.form("add_event_form", clear_on_submit=True):
        event_type = st.radio(
            "Payment Type",
            options=["expense", "investment"],
            format_func=lambda x: "💸 Expense" if x == "expense" else "📈 Investment",
            horizontal=True,
        )
        categories = _categories_for_type(event_type)

        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("Payment Name *", placeholder="e.g. Monthly Rent, Netflix, Daily Coffee")
            amount = st.number_input(
                f"Amount ({config.CURRENCY_SYMBOL}) *",
                min_value=0.01,
                value=500.0,
                step=0.01,
                format="%.2f",
            )
        with col2:
            category = st.selectbox("Category *", categories)
            if frequency == "monthly":
                day_of_month = st.number_input(
                    "Day of Month *",
                    min_value=1,
                    max_value=28,
                    value=1,
                    help="Max 28 so it's valid every month including February.",
                )
            else:
                day_of_month = 1

        description = st.text_input("Description / Note", placeholder="Optional extra detail")
        submitted = st.form_submit_button("🗓️ Create Payment", width='stretch', type="primary")

    if submitted:
        if not title.strip():
            st.error("❌ Payment name cannot be empty.")
        elif amount <= 0:
            st.error("❌ Amount must be greater than zero.")
        else:
            ok = EventModel.create_event(
                title, category, amount, int(day_of_month),
                description, event_type=event_type, frequency=frequency,
            )
            if ok:
                freq_label = "daily" if frequency == "daily" else "monthly"
                st.success(f"✅ Recurring {freq_label} payment **'{title.strip()}'** created successfully!")
                st.balloons()
            else:
                st.error("❌ Failed to create payment. Please try again.")


def render_scheduler_panel():
    st.subheader("⚡ Scheduler Status")

    today = date.today()
    now = datetime.now()
    st.markdown(
        f"**Today:** {today.strftime('%A, %d %B %Y')}  |  **Time:** {now.strftime('%H:%M')}"
    )
    st.divider()

    results = EventModel.run_due_events()
    if not results:
        st.info("No active recurring payments found. Add one in the **Add Payment** tab.")
        return

    counts = {"executed": 0, "skipped": 0, "pending": 0, "next_month": 0, "failed": 0}
    for r in results:
        counts[r["status"]] += 1

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("✅ Executed", counts["executed"])
    c2.metric("⏭️ Skipped", counts["skipped"])
    c3.metric("⏳ Pending", counts["pending"])
    c4.metric("🔜 Next Month", counts["next_month"])
    c5.metric("❌ Failed", counts["failed"])

    st.divider()
    st.markdown("#### Payment-by-Payment Status")

    status_icon = {"executed": "✅", "skipped": "⏭️", "pending": "⏳", "next_month": "🔜", "failed": "❌"}
    for r in results:
        ev = r["event"]
        frequency = ev.get("frequency", "monthly")
        next_due = r.get("next_due")
        next_due_str = f" · next: {next_due.strftime('%d %b %Y')}" if next_due else ""
        freq_badge = "🔁 Daily" if frequency == "daily" else "📅 Monthly"
        amount_period = "day" if frequency == "daily" else "month"
        st.markdown(
            f"{status_icon.get(r['status'], '❓')} **{ev['title']}** [{freq_badge}] — {r['reason']}  "
            f"<span style='color:#888;font-size:0.85rem;'>"
            f"(scheduled {r['due_date'].strftime('%d %b')}{next_due_str}, "
            f"{format_currency(ev['amount'])} / {amount_period})</span>",
            unsafe_allow_html=True,
        )

    st.divider()
    st.markdown("#### 🔁 Force Re-run Today")
    st.warning(
        "⚠️ This will re-create expense entries for **all active payments** even if they "
        "already ran today / this month. Use only to correct missing entries."
    )
    if st.button("🔁 Force Execute All Payments Now", type="primary"):
        force_results = EventModel.run_due_events(force=True)
        executed = [r for r in force_results if r["status"] == "executed"]
        failed = [r for r in force_results if r["status"] == "failed"]
        if executed:
            st.success(f"✅ Re-executed {len(executed)} payment(s).")
        if failed:
            st.error(f"❌ {len(failed)} payment(s) failed.")
        if not executed and not failed:
            st.info("No payments to execute.")
        st.rerun()


def _ordinal(n: int) -> str:
    if 11 <= (n % 100) <= 13:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")

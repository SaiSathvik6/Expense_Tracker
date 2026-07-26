import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import config
from database.models import ExpenseModel
from database.investment_model import InvestmentModel
from database.category_model import CategoryModel
from database.investment_category_model import InvestmentCategoryModel
from database.connection import get_db
from utils.helpers import get_current_month_range


def render_settings():
    st.header("⚙️ Settings")
    tab1, tab2, tab3, tab4 = st.tabs([
        "📦 Expense Categories",
        "📈 Investment Categories",
        "📥 Export Data",
        "🔄 Migrate Investments",
    ])
    with tab1:
        render_category_management()
    with tab2:
        render_investment_category_management()
    with tab3:
        render_export_section()
    with tab4:
        render_migration_section()


def render_category_management():
    all_categories = CategoryModel.get_all_categories()

    st.info(f"**Current Categories ({len(all_categories)}):**")
    cols = st.columns(3)
    for idx, category in enumerate(all_categories):
        with cols[idx % 3]:
            if category in config.CATEGORIES:
                st.markdown(f"• {category} ⭐")
            else:
                st.markdown(f"• {category}")
    st.caption("⭐ = Default categories")
    st.divider()

    st.markdown("### ➕ Add New Category")
    with st.form("add_category_form"):
        new_category = st.text_input(
            "Category Name",
            placeholder="e.g., Healthcare, Education, Entertainment",
        )
        submitted = st.form_submit_button("➕ Add Category", width='stretch')
        if submitted:
            if not new_category or not new_category.strip():
                st.error("❌ Category name cannot be empty!")
            elif new_category.strip().capitalize() in all_categories:
                st.error(f"❌ Category '{new_category.strip().capitalize()}' already exists!")
            elif len(new_category.strip()) > 30:
                st.error("❌ Category name is too long (max 30 characters)!")
            else:
                new_cat_name = new_category.strip().capitalize()
                if CategoryModel.add_category(new_cat_name):
                    st.success(f"✅ Category '{new_cat_name}' added successfully!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Failed to add category. Please try again.")

    st.divider()
    st.markdown("### 🗑️ Remove Category")

    db = get_db()
    custom_cats = db["categories"].find_one({"_id": "custom_categories"})
    custom_categories = custom_cats.get("categories", []) if custom_cats else []

    if not custom_categories:
        st.info("ℹ️ No custom categories to remove. Default categories cannot be removed.")
    else:
        with st.form("remove_category_form"):
            category_to_remove = st.selectbox(
                "Select Custom Category to Remove",
                options=custom_categories,
            )
            remove_submitted = st.form_submit_button("🗑️ Remove Category", type="primary", width='stretch')
            if remove_submitted:
                if CategoryModel.remove_category(category_to_remove):
                    st.success(f"✅ Category '{category_to_remove}' removed!")
                    st.info("ℹ️ Existing expenses with this category are preserved.")
                    st.rerun()
                else:
                    st.error("❌ Failed to remove category. Default categories cannot be removed.")


def render_investment_category_management():
    all_categories = InvestmentCategoryModel.get_all_categories()

    st.info(f"**Current Investment Categories ({len(all_categories)}):**")
    cols = st.columns(3)
    for idx, category in enumerate(all_categories):
        with cols[idx % 3]:
            if category in config.INVESTMENT_CATEGORIES:
                st.markdown(f"• {category} ⭐")
            else:
                st.markdown(f"• {category}")
    st.caption("⭐ = Default categories")
    st.divider()

    st.markdown("### ➕ Add New Investment Category")
    with st.form("add_investment_category_form"):
        new_category = st.text_input(
            "Category Name",
            placeholder="e.g., Crypto, Real Estate, Bonds",
        )
        submitted = st.form_submit_button("➕ Add Category", width='stretch')
        if submitted:
            if not new_category or not new_category.strip():
                st.error("❌ Category name cannot be empty!")
            elif new_category.strip().capitalize() in all_categories:
                st.error(f"❌ Category '{new_category.strip().capitalize()}' already exists!")
            elif len(new_category.strip()) > 30:
                st.error("❌ Category name is too long (max 30 characters)!")
            else:
                new_cat_name = new_category.strip().capitalize()
                if InvestmentCategoryModel.add_category(new_cat_name):
                    st.success(f"✅ Category '{new_cat_name}' added successfully!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Failed to add category. Please try again.")

    st.divider()
    st.markdown("### 🗑️ Remove Investment Category")

    db = get_db()
    custom_doc = db["investment_categories"].find_one({"_id": "custom_investment_categories"})
    custom_categories = custom_doc.get("categories", []) if custom_doc else []

    if not custom_categories:
        st.info("ℹ️ No custom investment categories to remove. Default categories cannot be removed.")
    else:
        with st.form("remove_investment_category_form"):
            category_to_remove = st.selectbox(
                "Select Custom Category to Remove",
                options=custom_categories,
            )
            remove_submitted = st.form_submit_button("🗑️ Remove Category", type="primary", width='stretch')
            if remove_submitted:
                if InvestmentCategoryModel.remove_category(category_to_remove):
                    st.success(f"✅ Category '{category_to_remove}' removed!")
                    st.info("ℹ️ Existing investments with this category are preserved.")
                    st.rerun()
                else:
                    st.error("❌ Failed to remove category. Default categories cannot be removed.")


def render_export_section():
    st.subheader("📥 Export Data")

    col1, col2 = st.columns(2)
    with col1:
        export_period = st.selectbox(
            "Select Period",
            options=["Current Month", "Last 3 Months", "Last 6 Months", "Current Year", "All Time"],
        )
    with col2:
        st.write("")
        st.write("")
        export_button = st.button("📊 Generate CSV", width='stretch')

    if export_button:
        now = datetime.now()
        if export_period == "Current Month":
            start_date, end_date = get_current_month_range()
        elif export_period == "Last 3 Months":
            start_date, end_date = now - timedelta(days=90), now
        elif export_period == "Last 6 Months":
            start_date, end_date = now - timedelta(days=180), now
        elif export_period == "Current Year":
            start_date, end_date = datetime(now.year, 1, 1), now
        else:
            start_date, end_date = None, None

        expenses = ExpenseModel.get_expenses(start_date, end_date)

        if not expenses:
            st.warning("No expenses found for the selected period.")
        else:
            df = pd.DataFrame(expenses)
            df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
            df = df[["date", "category", "description", "amount"]]
            df.columns = ["Date", "Category", "Description", "Amount"]
            csv = df.to_csv(index=False)

            st.download_button(
                label="⬇️ Download CSV",
                data=csv,
                file_name=f"expenses_{export_period.lower().replace(' ', '_')}_{now.strftime('%Y%m%d')}.csv",
                mime="text/csv",
                width='stretch',
            )
            st.success(f"✅ Found {len(expenses)} expenses for {export_period.lower()}!")
            with st.expander("📋 Preview Data"):
                st.dataframe(df, width='stretch', hide_index=True)


def _normalize_investment_category(raw: str) -> str:
    mapping = {
        "mutual fund": "Mutual Fund",
        "fd": "Fixed Deposit",
        "fixed deposit": "Fixed Deposit",
        "fixed fd": "Fixed Deposit",
        "sip": "SIP",
        "stocks": "Stocks",
        "ppf": "PPF",
        "nps": "NPS",
        "gold": "Gold",
        "other investment": "Other Investment",
    }
    return mapping.get(raw.strip().lower(), raw.strip())


def render_migration_section():
    st.subheader("🔄 Migrate Misclassified Investments")
    st.markdown(
        "This scans your **Expenses** for entries whose category matches an investment category "
        "(Mutual Fund, SIP, Stocks, PPF, NPS, Gold, Fixed Deposit, Other Investment) "
        "and moves them to the **Investments** collection."
    )

    candidates = ExpenseModel.get_expenses_by_categories(config.INVESTMENT_CATEGORIES)

    if not candidates:
        st.success("✅ No misclassified investment entries found in Expenses.")
        return

    st.warning(f"Found **{len(candidates)}** expense(s) that look like investments:")

    currency = config.CURRENCY_SYMBOL
    rows = []
    for exp in candidates:
        date_str = exp["date"].strftime("%d %b %Y") if hasattr(exp["date"], "strftime") else str(exp["date"])
        rows.append({
            "Date": date_str,
            "Category": exp.get("category", "—"),
            "Description": exp.get("description") or "—",
            "Amount": f"{currency}{exp['amount']:,.2f}",
        })

    st.dataframe(pd.DataFrame(rows), width='stretch', hide_index=True)

    st.divider()
    st.markdown(
        f"Clicking **Migrate All** will move all **{len(candidates)}** entries above "
        "from Expenses → Investments. This cannot be undone automatically."
    )

    col1, col2 = st.columns([1, 3])
    with col1:
        confirm = st.button("🚀 Migrate All", type="primary", width='stretch')

    if confirm:
        migrated, failed = 0, 0
        for exp in candidates:
            category = _normalize_investment_category(exp["category"])
            ok = InvestmentModel.create_investment(
                date=exp["date"],
                category=category,
                description=exp.get("description", ""),
                amount=exp["amount"],
            )
            if ok:
                ExpenseModel.delete_expense(str(exp["_id"]))
                migrated += 1
            else:
                failed += 1

        if migrated:
            st.success(f"✅ Successfully migrated {migrated} expense(s) to Investments.")
        if failed:
            st.error(f"❌ {failed} entries failed to migrate — they remain in Expenses.")
        st.rerun()

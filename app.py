import streamlit as st
import config
from components.dashboard import render_dashboard
from components.settings import render_settings
from components.transactions import render_transactions
from components.payments import render_payments
from components.investments import render_investments
from database.event_model import EventModel


st.set_page_config(
    page_title=config.PAGE_TITLE,
    page_icon=config.PAGE_ICON,
    layout=config.LAYOUT,
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main { padding-top: 2rem; }
    .stMetric {
        background-color: #000000;
        color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border: 1px solid #333;
    }
    [data-testid="stMetricLabel"] { color: #cccccc !important; }
    [data-testid="stMetricValue"] { color: #ffffff !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 2rem; }
    .stTabs [data-baseweb="tab"] { padding: 1rem 2rem; font-weight: 600; }
    div[data-testid="stExpander"] {
        background-color: #1e1e1e;
        border-radius: 0.5rem;
        border: 1px solid #333;
    }
    div[data-testid="stExpander"] details { background-color: #1e1e1e; }
    div[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
        background-color: #1e1e1e;
        color: #ffffff;
    }
</style>
""", unsafe_allow_html=True)

VALID_PAGES = {"Dashboard", "Transactions", "Investments", "Settings", "Payments"}

if "page" not in st.session_state:
    qp = st.query_params.get("page", "Dashboard")
    st.session_state.page = qp if qp in VALID_PAGES else "Dashboard"

st.query_params["page"] = st.session_state.page

try:
    EventModel.run_due_events()
except Exception:
    pass


def navigate(page: str):
    st.session_state.page = page
    st.query_params["page"] = page
    if "editing_expense" in st.session_state:
        del st.session_state.editing_expense
    st.rerun()


with st.sidebar:
    st.title(f"{config.PAGE_ICON} Expense Tracker")
    st.markdown("---")

    current = st.session_state.page

    if st.button("📊 Dashboard", width='stretch',
                 type="primary" if current == "Dashboard" else "secondary"):
        navigate("Dashboard")
    if st.button("💳 Transactions", width='stretch',
                 type="primary" if current == "Transactions" else "secondary"):
        navigate("Transactions")
    if st.button("📈 Investments", width='stretch',
                 type="primary" if current == "Investments" else "secondary"):
        navigate("Investments")
    if st.button("🗓️ Payments", width='stretch',
                 type="primary" if current == "Payments" else "secondary"):
        navigate("Payments")
    if st.button("⚙️ Settings", width='stretch',
                 type="primary" if current == "Settings" else "secondary"):
        navigate("Settings")

    st.markdown("---")

try:
    if st.session_state.page == "Dashboard":
        render_dashboard()
    elif st.session_state.page == "Transactions":
        render_transactions()
    elif st.session_state.page == "Investments":
        render_investments()
    elif st.session_state.page == "Payments":
        render_payments()
    elif st.session_state.page == "Settings":
        render_settings()
except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    st.exception(e)
    st.stop()

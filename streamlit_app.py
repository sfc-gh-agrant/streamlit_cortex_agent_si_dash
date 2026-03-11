import streamlit as st
import pandas as pd
import numpy as np
from snowflake.snowpark.context import get_active_session
from datetime import datetime, timedelta

session = get_active_session()

st.set_page_config(layout="wide", page_title="AI Usage Monitor")

ACCENT = "#4A90D9"
GOOD = "#2ECC71"
WARN = "#F39C12"

st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #f0f4fa 0%, #e8edf5 100%);
        border: 1px solid #d0d8e8;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    }
    .metric-value { font-size: 2rem; font-weight: 700; }
    .metric-label { font-size: 0.85rem; color: #5a6a7a; margin-top: 4px; }
    .section-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: #2c3e50;
        border-left: 3px solid #4A90D9;
        padding-left: 10px;
        margin: 24px 0 12px 0;
    }
    div[data-testid="stDataFrame"] { border: 1px solid #d0d8e8; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

st.markdown("# :bar_chart: AI Usage Monitoring Dashboard")
st.markdown("---")

USE_SIMULATED = st.checkbox("Use Simulated Data (demo with 250 users)", value=True)

ROLES = ["DATA_ENGINEER", "DATA_SCIENTIST", "ANALYST", "DEVELOPER", "PRODUCT_MANAGER", "FINANCE", "HR", "EXEC"]
BUSINESS_AREAS = ["Engineering", "Analytics", "Finance", "Operations", "Marketing", "Sales", "HR", "Executive"]

def generate_simulated_data(source_type, n_users=250, n_requests=5000):
    np.random.seed(42 if source_type == "intel" else 99)
    users = [f"USER_{i:03d}" for i in range(1, n_users + 1)]
    agents = (
        ["SALES_ANALYST", "INVENTORY_AGENT", "HR_ASSISTANT", "FINANCE_BOT", "SUPPORT_AGENT", "DATA_EXPLORER", "REPORT_GEN"]
        if source_type == "intel"
        else ["CODE_ASSISTANT", "SQL_HELPER", "DOC_SEARCH", "CHAT_AGENT", "SUMMARIZER", "TRANSLATOR", "QA_BOT"]
    )
    databases = ["PROD_DB", "ANALYTICS_DB", "STAGING_DB", "WAREHOUSE_DB"]

    base = datetime(2025, 10, 1)
    days = (datetime(2026, 3, 11) - base).days

    user_picks = np.random.choice(users, n_requests)
    agent_picks = np.random.choice(agents, n_requests)
    start_times = [base + timedelta(days=int(np.random.randint(0, days)), hours=int(np.random.randint(0, 24)), minutes=int(np.random.randint(0, 60))) for _ in range(n_requests)]
    tokens = np.random.randint(100, 200000, n_requests)
    credits = np.random.uniform(0.0001, 0.25, n_requests)

    user_role_map = {u: np.random.choice(ROLES) for u in users}
    user_area_map = {u: np.random.choice(BUSINESS_AREAS) for u in users}

    df = pd.DataFrame({
        "START_TIME": start_times,
        "END_TIME": [t + timedelta(seconds=int(np.random.randint(2, 30))) for t in start_times],
        "USER_NAME": user_picks,
        "ROLE_NAME": [user_role_map[u] for u in user_picks],
        "BUSINESS_AREA": [user_area_map[u] for u in user_picks],
        "AGENT_DATABASE_NAME": np.random.choice(databases, n_requests),
        "AGENT_SCHEMA_NAME": "PUBLIC",
        "AGENT_NAME": agent_picks,
        "TOKEN_CREDITS": credits,
        "TOKENS": tokens,
        "REQUEST_ID": [f"{np.random.randint(int(1e8), int(1e9))}" for _ in range(n_requests)],
    })
    if source_type == "intel":
        df["SNOWFLAKE_INTELLIGENCE_NAME"] = np.random.choice(["SI_PROD", "SI_DEV", "SI_STAGING"], n_requests)
    return df.sort_values("START_TIME", ascending=False).reset_index(drop=True)

def load_real_data(view_name, extra_cols=""):
    df = session.sql(f"""
        SELECT START_TIME, END_TIME, USER_NAME, {extra_cols}
            AGENT_DATABASE_NAME, AGENT_SCHEMA_NAME, AGENT_NAME,
            TOKEN_CREDITS, TOKENS, REQUEST_ID, METADATA
        FROM SNOWFLAKE.ACCOUNT_USAGE.{view_name}
        ORDER BY START_TIME DESC
    """).to_pandas()
    if not df.empty and "METADATA" in df.columns:
        df["ROLE_NAME"] = df["METADATA"].apply(lambda x: x.get("role_name") if isinstance(x, dict) else None)
        df["ROLE_NAME"] = df["ROLE_NAME"].fillna("N/A")
    else:
        df["ROLE_NAME"] = "N/A"
    df["BUSINESS_AREA"] = "N/A"
    return df

def metric_card(label, value, color="#333333"):
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value" style="color:{color}">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """, unsafe_allow_html=True)

def render_tab(df, label):
    if df.empty:
        st.info(f"No {label} usage data found.")
        return

    total_credits = df["TOKEN_CREDITS"].sum()
    total_tokens = df["TOKENS"].sum()
    total_requests = len(df)
    unique_users = df["USER_NAME"].nunique()
    unique_agents = df["AGENT_NAME"].nunique()

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1: metric_card("Total Requests", f"{total_requests:,}", ACCENT)
    with k2: metric_card("Total Credits", f"{total_credits:,.4f}", WARN)
    with k3: metric_card("Total Tokens", f"{total_tokens:,.0f}", GOOD)
    with k4: metric_card("Unique Users", f"{unique_users}", "#7C3AED")
    with k5: metric_card("Active Agents", f"{unique_agents}", "#DB2777")

    st.markdown("")

    st.markdown('<div class="section-header">Top 10 Users by Credit Consumption</div>', unsafe_allow_html=True)
    top_users = df.groupby("USER_NAME").agg(
        CREDITS=("TOKEN_CREDITS", "sum"),
        REQUESTS=("REQUEST_ID", "count"),
        TOKENS=("TOKENS", "sum"),
        ROLE=("ROLE_NAME", "first"),
        AREA=("BUSINESS_AREA", "first"),
        TOP_AGENT=("AGENT_NAME", lambda x: x.value_counts().index[0])
    ).sort_values("CREDITS", ascending=False).head(10).reset_index()
    top_users.columns = ["User", "Credits", "Requests", "Tokens", "Role", "Business Area", "Most Used Agent"]

    tu_left, tu_right = st.columns([2, 3])
    with tu_left:
        chart_df = top_users[["User", "Credits"]].set_index("User")
        st.bar_chart(chart_df)
    with tu_right:
        display_df = top_users.copy()
        display_df["Credits"] = display_df["Credits"].apply(lambda x: f"{x:.4f}")
        display_df["Tokens"] = display_df["Tokens"].apply(lambda x: f"{x:,.0f}")
        display_df["Requests"] = display_df["Requests"].apply(lambda x: f"{x:,}")
        st.dataframe(display_df, use_container_width=True)

    left_col, right_col = st.columns(2)
    with left_col:
        st.markdown('<div class="section-header">Usage by Role</div>', unsafe_allow_html=True)
        by_role = df.groupby("ROLE_NAME")["TOKEN_CREDITS"].sum().sort_values(ascending=False)
        st.bar_chart(by_role)

    with right_col:
        st.markdown('<div class="section-header">Usage by Business Area</div>', unsafe_allow_html=True)
        by_area = df.groupby("BUSINESS_AREA")["TOKEN_CREDITS"].sum().sort_values(ascending=False)
        st.bar_chart(by_area)

    st.markdown('<div class="section-header">User-Agent Credit Matrix (Top 15 Users x Agents)</div>', unsafe_allow_html=True)
    top15 = df.groupby("USER_NAME")["TOKEN_CREDITS"].sum().sort_values(ascending=False).head(15).index.tolist()
    heatmap_df = df[df["USER_NAME"].isin(top15)].groupby(["USER_NAME", "AGENT_NAME"])["TOKEN_CREDITS"].sum().reset_index()
    pivot = heatmap_df.pivot_table(index="USER_NAME", columns="AGENT_NAME", values="TOKEN_CREDITS", fill_value=0)
    pivot = pivot.round(4)
    st.dataframe(pivot, use_container_width=True)

    ts = df.copy()
    ts["DATE"] = pd.to_datetime(ts["START_TIME"]).dt.date

    daily = ts.groupby("DATE").agg(
        CREDITS=("TOKEN_CREDITS", "sum"),
        REQUESTS=("REQUEST_ID", "count"),
        TOKENS=("TOKENS", "sum")
    ).reset_index().sort_values("DATE").set_index("DATE")

    st.markdown('<div class="section-header">Credits Over Time</div>', unsafe_allow_html=True)
    st.area_chart(daily[["CREDITS"]])

    c_left, c_right = st.columns(2)
    with c_left:
        st.markdown('<div class="section-header">Credits by Agent</div>', unsafe_allow_html=True)
        by_agent = ts.groupby("AGENT_NAME")["TOKEN_CREDITS"].sum().sort_values(ascending=False)
        st.bar_chart(by_agent)
    with c_right:
        st.markdown('<div class="section-header">Daily Request Volume</div>', unsafe_allow_html=True)
        st.bar_chart(daily[["REQUESTS"]])

    st.markdown('<div class="section-header">Avg Tokens per Agent</div>', unsafe_allow_html=True)
    avg_tok = ts.groupby("AGENT_NAME")["TOKENS"].mean().sort_values(ascending=False)
    st.bar_chart(avg_tok)

    st.markdown('<div class="section-header">Request Detail</div>', unsafe_allow_html=True)
    st.dataframe(df, use_container_width=True)

tab1, tab2 = st.tabs([":zap: Snowflake Intelligence", ":robot_face: Cortex Agent"])

with tab1:
    if USE_SIMULATED:
        df_intel = generate_simulated_data("intel")
    else:
        df_intel = load_real_data("SNOWFLAKE_INTELLIGENCE_USAGE_HISTORY", "SNOWFLAKE_INTELLIGENCE_NAME, ")
    render_tab(df_intel, "Snowflake Intelligence")

with tab2:
    if USE_SIMULATED:
        df_agent = generate_simulated_data("agent")
    else:
        df_agent = load_real_data("CORTEX_AGENT_USAGE_HISTORY", "")
    render_tab(df_agent, "Cortex Agent")

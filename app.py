# app.py
import os, time, hashlib
import pandas as pd
import sqlalchemy as sa
import streamlit as st
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase

from sql_only import build_sql_only_chain, run_sql_df  # you already have these
from guards import sanitize_sql                            # Phase 1 guards
from viz_guess import auto_chart                           # simple chart guess
from logger import log_event                               # Phase 1 logger

# ---------- Setup ----------
load_dotenv()
DB_URL = os.getenv("DATABASE_URL", "sqlite:///demo.db")

db = SQLDatabase.from_uri(DB_URL)
schema_text = db.get_table_info()

@st.cache_resource
def get_engine():
    return sa.create_engine(DB_URL)

dialect = get_engine().dialect.name
if dialect.startswith("postgres"):
    dialect = "postgres"

# Allow-list: include the tables you want users to touch
ALLOWED_TABLES = {"customers", "orders", "order_items", "products"}

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
sql_from_q = build_sql_only_chain(llm, schema_text, limit=1000)

@st.cache_data(ttl=300, show_spinner=False)  # cache results for 5 minutes

def cached_query(sql: str, params: dict | None = None):
    start = time.perf_counter()
    with get_engine().connect() as conn:
        df = pd.read_sql(sa.text(sql), conn, params=params)
    latency = int((time.perf_counter() - start) * 1000)
    return df, latency

def explain_df(question: str, sql: str, df: pd.DataFrame) -> str:
    """Tiny summary prompt on head() + schema to keep tokens low."""
    head = df.head(10).to_csv(index=False)
    schema_line = ", ".join([f"{c}:{str(df[c].dtype)}" for c in df.columns])
    prompt = f"""You are a concise data analyst.
User question: {question}
SQL used: {sql}
Columns: {schema_line}
Here are up to 10 top rows (CSV):
{head}

Write 3–5 crisp bullet insights (no code, no SQL), highlighting trends, top categories, or spikes. Keep it under 120 words total."""
    resp = llm.invoke(prompt)
    return resp.content.strip()

st.set_page_config(page_title="SQL Data Agent", layout="wide")
st.title("SQL Data Agent")

if "proceed" not in st.session_state:
    st.session_state.proceed = False



with st.sidebar:
    st.subheader("Settings")
    limit = st.number_input("Row LIMIT", min_value=50, max_value=10000, value=1000, step=50)
    approve = st.checkbox("Approve SQL before run", value=True)
    show_logs = st.checkbox("Log queries (CSV)", value=True)
    st.caption(f"DB: {DB_URL} | dialect: {dialect}")

tab1, tab2 = st.tabs(["SQL + Viz (deterministic)", "Explain (chatty)"])

# --------- Tab 1: Deterministic path ----------
# ---- init once ----
st.session_state.setdefault("safe_sql", None)
st.session_state.setdefault("show_run", False)   # whether to show the "Run" button

with tab1:
    st.subheader("Ask a question")
    q = st.text_input("e.g., Total revenue by region (quantity*unit_price), descending")

    # 1) Stage SQL on click, flip a persistent flag
    if st.button("Generate SQL") and q:
        raw_sql = sql_from_q(q)
        st.session_state.safe_sql = sanitize_sql(
            raw_sql, limit=limit, dialect=dialect, allowlist=ALLOWED_TABLES
        )
        st.session_state.show_run = True  # persist visibility of the Run button

    # 2) Always show staged SQL if present
    if st.session_state.safe_sql:
        st.code(st.session_state.safe_sql, language="sql")

    # 3) Approval flow
    should_execute = False
    if st.session_state.safe_sql:
        if approve:
            # Turn button click (event) into persistent state by setting a flag
            if st.button("Run this SQL now"):
                should_execute = True
        else:
            should_execute = True

    # 4) Execute (and optionally reset state)
    if should_execute and st.session_state.safe_sql:
        df, latency = cached_query(st.session_state.safe_sql)
        st.write(f"**Rows:** {len(df)} | **Latency:** {latency} ms")
        st.dataframe(df.head(200), use_container_width=True)
        fig = auto_chart(df)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        st.download_button("Download CSV", df.to_csv(index=False), "result.csv", "text/csv")

        if show_logs:
            log_event(user_q=q, sql=st.session_state.safe_sql, rows=len(df), ms=latency, ok=True)

        # reset if you want to go back to "Generate" step
        st.session_state.show_run = False
        # (keep safe_sql if you want it visible; set to None to clear)
        # st.session_state.safe_sql = None

# --------- Tab 2: Chatty explanation ----------
with tab2:
    st.subheader("Explain the result")
    q2 = st.text_input("Question for explanation", key="q2")
    go = st.button("Run (SQL → Data → Insight)")
    if go and q2:
        try:
            raw_sql = sql_from_q(q2)
            safe_sql = sanitize_sql(raw_sql, limit=limit, dialect=dialect, allowlist=ALLOWED_TABLES)
            st.code(safe_sql, language="sql")
            df, latency = cached_query(safe_sql)
            st.write(f"**Rows:** {len(df)} | **Latency:** {latency} ms")
            st.dataframe(df.head(200), use_container_width=True)

            insight = explain_df(q2, safe_sql, df)
            st.markdown(insight)

            fig = auto_chart(df)
            if fig:
                st.plotly_chart(fig, use_container_width=True)

            if show_logs:
                log_event(user_q=q2, sql=safe_sql, rows=len(df), ms=latency, ok=True)

        except Exception as e:
            st.error(str(e))
            if show_logs:
                log_event(user_q=q2, sql=locals().get("raw_sql", ""), rows=0, ms=0, ok=False, error=str(e))

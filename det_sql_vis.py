# det-sql-vis.py
import time
import sqlalchemy as sa
import pandas as pd
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from sql_only import build_sql_only_chain, run_sql_df
from guards import sanitize_sql
from logger import log_event

load_dotenv()

DB_URL = "sqlite:///demo.db"  # change to your DB if needed
engine = sa.create_engine(DB_URL)
db = SQLDatabase.from_uri(DB_URL)
schema_text = db.get_table_info()

# Map SQLAlchemy → sqlglot dialect names
dialect = engine.dialect.name  # "sqlite", "postgresql", "mysql", ...
if dialect.startswith("postgres"):
    dialect = "postgres"

# Allow-list (edit to match your DB)
ALLOWED_TABLES = {"customers", "orders", "order_items"}  # add "products" if present

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
sql_from_q = build_sql_only_chain(llm, schema_text, limit=1000)

def approve(sql: str) -> bool:
    print("\n--- SQL to run ---\n", sql, "\n------------------")
    return input("Run this? [y/N] ").strip().lower() == "y"

def answer(question: str, limit: int = 1000):
    start = time.perf_counter()
    rows = 0
    try:
        raw_sql = sql_from_q(question)  # LLM generates raw SELECT (no prose)
        safe_sql = sanitize_sql(raw_sql, limit=limit, dialect=dialect, allowlist=ALLOWED_TABLES)

        # approval gate
        if not approve(safe_sql):
            print("Cancelled.")
            return

        df = run_sql_df(engine, safe_sql)
        rows = len(df)
        elapsed = int((time.perf_counter() - start) * 1000)

        print("\nTop rows:\n", df.head(20))
        print(f"\nRows: {rows} | Latency: {elapsed} ms")
        log_event(user_q=question, sql=safe_sql, rows=rows, ms=elapsed, ok=True)

    except Exception as e:
        elapsed = int((time.perf_counter() - start) * 1000)
        print("Error:", e)
        log_event(user_q=question, sql=locals().get("raw_sql", ""), rows=rows, ms=elapsed, ok=False, error=str(e))

if __name__ == "__main__":
    q = "Total revenue by customer (quantity*unit_price), top 5"
    answer(q, limit=1000)

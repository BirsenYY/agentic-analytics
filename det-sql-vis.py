# run_det_sql_viz.py
import os, sqlalchemy as sa
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from sql_only import build_sql_only_chain, run_sql_df
from viz_guess import auto_chart

load_dotenv()
DB_URL = "sqlite:///demo.db"  # or your Postgres/MySQL URL
engine = sa.create_engine(DB_URL)
dialect = engine.dialect.name  
db = SQLDatabase.from_uri(DB_URL)

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
schema_text = db.get_table_info()
sql_from_q = build_sql_only_chain(llm, schema_text, limit=1000, dialect=dialect)

question = "Total revenue by region (quantity*unit_price), descending"
sql = sql_from_q(question)
print("SQL:\n", sql)

df = run_sql_df(engine, sql)
print("\nTop rows:\n", df.head())

try:
    fig = auto_chart(df)
    if fig: fig.show()
except Exception as e:
    print("Chart error:", e)

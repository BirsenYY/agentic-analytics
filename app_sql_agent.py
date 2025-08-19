# app_sql_agent.py
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent

load_dotenv()

# 1) DB (SQLite for MVP)
DB_URL = "sqlite:///demo.db"
db = SQLDatabase.from_uri(DB_URL)

# 2) LLM (use a low-cost, reliable model)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# 3) Create the agent
agent = create_sql_agent(
    llm=llm,
    db=db,
    agent_type="openai-tools",
    verbose=False,            # prints reasoning/tool calls to console
    use_query_checker=True,  # fixes small SQL mistakes
    top_k=5,                 # schema context size
    prefix=(
        "You are a SQL assistant.\n"
        "- Only run safe, read-only SELECT queries.\n"
        "- Use ONLY tables/columns that exist in the provided schema.\n"
        "- Always include LIMIT 1000 unless a smaller sample is requested.\n"
        "- Prefer ANSI SQL; avoid vendor-specific functions unless necessary."
    ),
)

# 4) Ask a few questions
questions = [
    "Show total revenue by region (quantity*unit_price), descending.",
    "Top 2 products by total quantity.",
    "Show monthly revenue trend with year-month."
]

for q in questions:
    print("\nQ:", q)
    resp = agent.invoke({"input": q})
    print("A:", resp["output"])

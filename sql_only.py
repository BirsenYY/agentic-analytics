# sql_only.py
import re
import pandas as pd
import sqlalchemy as sa
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from sqlglot import parse_one
from sqlglot.expressions import Limit, Literal

def strip_code_fences(text: str) -> str:
    return re.sub(r"^```(sql)?|```$", "", text.strip(), flags=re.IGNORECASE|re.MULTILINE)

def force_safe_select(sql: str, limit: int = 1000, dialect: str | None = None) -> str:
    tree = parse_one(sql, dialect)
    if tree.key.upper() != "SELECT":
        raise ValueError("Only SELECT queries are allowed")
    if not tree.find(Limit):
        tree.set("limit", Limit(this=Literal.number(limit)))
    return tree.sql(dialect=dialect)

def build_sql_only_chain(llm: ChatOpenAI, schema_text: str, limit: int = 1000, dialect: str | None = None ):
    prompt = ChatPromptTemplate.from_template(
        """You are a meticulous analytics engineer.
Write a single ANSI SQL SELECT statement that answers the question using ONLY the provided schema.
Rules:
- SELECT only (no INSERT/UPDATE/DELETE/DDL).
- Use only tables/columns from the schema.
- Always include LIMIT {limit}.
- Return ONLY raw SQL (no explanations, no markdown fences).

Schema:
{schema}

Question: {question}

SQL:"""
    )
    chain = prompt | llm | StrOutputParser()
    def sql_from_question(question: str) -> str:
        raw = chain.invoke({"schema": schema_text, "question": question, "limit": limit})
        return force_safe_select(strip_code_fences(raw), limit, dialect)
    return sql_from_question

def run_sql_df(engine: sa.Engine, sql: str) -> pd.DataFrame:
    with engine.connect() as conn:
        return pd.read_sql(sa.text(sql), conn)

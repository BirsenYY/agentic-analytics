# viz_guess.py
import pandas as pd
import plotly.express as px

def auto_chart(df: pd.DataFrame):
    if df.empty or df.shape[1] < 2:
        return None
    # simple heuristics
    if pd.api.types.is_datetime64_any_dtype(df.iloc[:,0]) or "date" in df.columns[0].lower():
        return px.line(df, x=df.columns[0], y=df.columns[1], title="Time series")
    if pd.api.types.is_numeric_dtype(df.iloc[:,1]) and not pd.api.types.is_numeric_dtype(df.iloc[:,0]):
        return px.bar(df, x=df.columns[0], y=df.columns[1], title="Categorical summary")
    # fallback
    return px.scatter(df, x=df.columns[0], y=df.columns[1], title="Scatter")

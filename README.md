# Agentic Analytics — Data Visualization with Built-in Agents  

## Overview  
This project demonstrates how large language models can be combined with **built-in LangChain agents** to query data and generate visualizations interactively. The application is built with **Streamlit** for the UI and uses **LangChain’s built-in SQL and Pandas dataframe agents** to translate natural language into structured queries and visual outputs.  

## Features  
- Natural language interface for data exploration.  
- Query execution via **SQLDatabaseChain / SQL Agent** (LangChain built-in).  
- Data manipulation and visualization via **Pandas DataFrame Agent**.  
- Caching layer (`st.cache_data`) for performance.  
- Streamlit frontend for interactivity.  

## How It Works  
1. User submits a natural language question.  
2. A built-in agent interprets the query.  
3. If SQL is needed, the **SQL Agent** generates and executes queries against the database.  
4. If visualization is requested, the **Pandas Agent** processes the DataFrame and returns a plot.  
5. Results are displayed in Streamlit.  

## Limitations of Using Built-in Agents  
While this setup works, it comes with important limitations:  

1. **Opaque Planning**  
   - Tool selection and reasoning are hidden inside LangChain.  
   - Hard to trace why an agent chose a certain path.  

2. **Limited Control**  
   - No fine-grained control over the planning/execution loop.  
   - Difficult to enforce strict constraints (e.g., SQL safety, budget caps).  

3. **Reproducibility Issues**  
   - Agents may generate slightly different outputs for the same input, depending on randomness (temperature, context).  

4. **Shallow Memory**  
   - Built-in agents do not persist preferences or context across sessions.  
   - No semantic memory for user-specific defaults (e.g., preferred chart type).  

5. **Safety & Governance Gaps**  
   - Reliant on LangChain’s defaults for SQL sanitization and tool usage.  
   - Harder to implement reflection/validation of results.  

6. **Evaluation Challenges**  
   - Limited hooks to evaluate agent reasoning, measure cost/latency, or run adversarial robustness tests.  

## Next Steps — Toward Custom Agents  
The next version of this project will move beyond built-in agents by:  
- Designing a **custom planner/executor loop** (deterministic state machine).  
- Adding **reflection and repair** steps for more reliable outputs.  
- Defining **typed tool contracts** with schemas for safe execution.  
- Implementing **memory** (episodic + semantic) for personalization.  
- Introducing **evaluation metrics** for accuracy, cost, and latency.  

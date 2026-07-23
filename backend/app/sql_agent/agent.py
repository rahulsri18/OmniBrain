"""
agent.py - SQL Sub-Agent Node
Generates SQL from Natural Language AND executes it safely using ReadOnlySQLDatabase.
"""

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.logger import logger
from app.sql_agent.db import ReadOnlySQLDatabase
from app.sql_agent.prompts import SQL_SYSTEM_PROMPT

llm = ChatOpenAI(model="gpt-4o", temperature=0)

# Local SQLite DB instance (update db_path if needed)
db_client = ReadOnlySQLDatabase(db_path="data/sqlite.db")


def sql_agent_node(question: str) -> dict:
    """Converts natural language question into SQL, executes it, and returns results."""
    try:
        messages = [
            SystemMessage(content=SQL_SYSTEM_PROMPT),
            HumanMessage(content=question),
        ]

        response = llm.invoke(messages)
        sql_query = response.content.strip()

        # Clean markdown code blocks if LLM wraps SQL in ```sql ... ```
        if sql_query.startswith("```"):
            sql_query = (
                sql_query.replace("```sql", "")
                .replace("```", "")
                .strip()
            )

        logger.info(f"Generated SQL Query: {sql_query}")

        # Execute safe query via ReadOnlySQLDatabase (M2's Module)
        db_results = db_client.execute_query(sql_query)

        return {
            "sql_query": sql_query,
            "data": db_results,
            "error": None,
        }

    except Exception as e:
        logger.error(f"SQL Agent Error: {str(e)}")
        return {
            "sql_query": "",
            "data": [],
            "error": str(e),
        }
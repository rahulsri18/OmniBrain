from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from backend.app.sql_agent.prompts import SQL_SYSTEM_PROMPT

llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0
)

def sql_agent_node(question: str) -> str:
    """
    Convert a natural language question into a SQL query.
    """

    messages = [
        SystemMessage(content=SQL_SYSTEM_PROMPT),
        HumanMessage(content=question),
    ]

    response = llm.invoke(messages)

    return response.content.strip()
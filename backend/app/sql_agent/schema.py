from typing import TypedDict
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


class SQLAgentState(TypedDict):
    """
    State used by the SQL Agent.
    """

    question: str
    sql_query: str
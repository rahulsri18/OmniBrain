from typing import TypedDict


class SQLAgentState(TypedDict):
    """
    State used by the SQL Agent.
    """

    question: str
    sql_query: str
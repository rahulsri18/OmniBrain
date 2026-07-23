from typing import TypedDict
from typing import Optional
from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


class SQLAgentState(TypedDict):
    """
    State used by the SQL Agent.
    """

    question: str
    sql_query: str
    session_id: Optional[str] = None
    file_path: Optional[str] = None  # Optional field for attached document/image path
    

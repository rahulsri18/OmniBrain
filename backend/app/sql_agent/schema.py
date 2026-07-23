from typing import Optional
from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    file_path: Optional[str] = None  # Optional field for attached document/image path
    
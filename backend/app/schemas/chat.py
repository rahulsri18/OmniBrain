from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ChatRequest(BaseModel):
    message: str = Field(..., description="User's query or message", example="Summarize the annual report")
    session_id: Optional[str] = Field(None, description="Unique session ID for tracking history")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "What are the key highlights of the uploaded document?",
                "session_id": "session_a1b2c3d4e5f6"
            }
        }


class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the sender: 'user' or 'assistant'")
    content: str = Field(..., description="Text content of the message")
    timestamp: Optional[float] = Field(None, description="Unix timestamp of when message was sent")


class SessionResponse(BaseModel):
    session_id: str
    user_id: str
    history: List[ChatMessage] = []
    created_at: float
    updated_at: float
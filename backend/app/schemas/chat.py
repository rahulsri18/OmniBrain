from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class ChatRequest(BaseModel):
    """
    यूजर द्वारा चैट एंडपॉइंट (/api/v1/chat) पर भेजे जाने वाले डेटा का स्कीमा
    """
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
    """
    सिंगल चैट मैसेज का स्ट्रक्चर
    """
    role: str = Field(..., description="Role of the sender: 'user' or 'assistant'")
    content: str = Field(..., description="Text content of the message")
    timestamp: Optional[float] = Field(None, description="Unix timestamp of when message was sent")


class SessionResponse(BaseModel):
    """
    सेशन डिटेल्स और चैट हिस्ट्री रिटर्न करने के लिए स्कीमा
    """
    session_id: str
    user_id: str
    history: List[ChatMessage] = []
    created_at: float
    updated_at: float
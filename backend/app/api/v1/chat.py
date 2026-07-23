"""
chat.py

API Controller / Endpoint for Chat streaming.
Integrates FastAPI with the compiled LangGraph workflow.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import json
from typing import AsyncGenerator, Optional

# 🎯 यहाँ पाथ चेंज किया गया है (क्योंकि agents डायरेक्ट backend/ के अंदर है)
from agents.graph import app_graph  # Directly importing from backend/agents/graph.py
from app.logger import logger

router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(..., description="User prompt or question")
    session_id: str = Field(..., description="Unique chat session ID")
    file_path: Optional[str] = Field(None, description="Optional attached document/image path")


async def stream_graph_response(user_message: str, session_id: str, file_path: Optional[str] = None) -> AsyncGenerator[str, None]:
    """
    Middleware generator that executes the compiled LangGraph agent 
    and streams back response chunks as Server-Sent Events (SSE).
    """
    try:
        # 1. Initial State Definition for LangGraph
        initial_state = {
            "messages": [{"role": "user", "content": user_message}],
            "session_id": session_id,
            "file_path": file_path,
            "next_node": ""
        }

        # 2. Invoke / Stream graph events
        async for event in app_graph.astream_events(initial_state, version="v2"):
            kind = event.get("event")

            # Stream LLM generation tokens directly to frontend
            if kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if hasattr(chunk, "content") and chunk.content:
                    yield f"data: {json.dumps({'content': chunk.content})}\n\n"

            elif kind == "on_chain_start" and event.get("name") in ["rag_node", "sql_node", "vision_node"]:
                logger.info(f"Session {session_id}: Executing LangGraph Node -> {event['name']}")

        # Signal end of stream
        yield f"data: {json.dumps({'type': 'telemetry', 'step': event['name']})}\n\n"

    except Exception as e:
        logger.error(f"Error during LangGraph streaming execution for session {session_id}: {str(e)}")
        err_msg = json.dumps({"error": "An error occurred while processing your query."})
        yield f"data: {err_msg}\n\n"


@router.post("/chat")
async def chat_endpoint(request: ChatRequest):
    """
    Chat API Endpoint that invokes the compiled LangGraph agent middleware
    and streams response back using Server-Sent Events (SSE).
    """
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    logger.info(f"Received chat request for session: {request.session_id}")

    return StreamingResponse(
        stream_graph_response(
            user_message=request.message,
            session_id=request.session_id,
            file_path=request.file_path
        ),
        media_type="text/event-stream"
    )
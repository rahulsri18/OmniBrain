"""
chat.py

API Controller / Endpoint for Chat streaming.
Integrates FastAPI with the compiled LangGraph workflow and streams 
both LLM tokens and Agent Reasoning / Steps.
"""

import json
from typing import AsyncGenerator, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# Importing graph from backend/agents/graph.py
from agents.graph import app_graph
from app.logger import logger

router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(..., description="User prompt or question")
    session_id: str = Field(..., description="Unique chat session ID")
    file_path: Optional[str] = Field(None, description="Optional attached document/image path")


async def stream_graph_response(
    user_message: str, 
    session_id: str, 
    file_path: Optional[str] = None
) -> AsyncGenerator[str, None]:
    """
    Middleware generator that executes the compiled LangGraph agent 
    and streams back response chunks along with agent reasoning as SSE.
    """
    try:
        # 1. Initial State Definition for LangGraph
        initial_state = {
            "messages": [{"role": "user", "content": user_message}],
            "session_id": session_id,
            "file_path": file_path,
            "next_node": ""
        }

        current_active_node = "supervisor"

        # 2. Stream graph events from LangGraph
        async for event in app_graph.astream_events(initial_state, version="v2"):
            kind = event.get("event")
            name = event.get("name", "")

            # 🧠 A. Emit Reasoning / Agent Step when a new node starts executing
            if kind == "on_chain_start" and name in ["supervisor", "rag_node", "sql_node", "vision_node"]:
                current_active_node = name
                reasoning_msg = f"Agent routing to or processing in node: '{name}'"
                logger.info(f"Session {session_id}: Executing Node -> {name}")

                yield f"data: {json.dumps({'type': 'reasoning', 'thought': reasoning_msg, 'node': name})}\n\n"

            # 💬 B. Stream LLM text tokens directly to frontend
            elif kind == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                if hasattr(chunk, "content") and chunk.content:
                    yield f"data: {json.dumps({'type': 'content', 'content': chunk.content, 'node': current_active_node})}\n\n"

        # 🏁 C. Signal end of stream
        yield f"data: {json.dumps({'type': 'status', 'status': 'completed', 'step': current_active_node})}\n\n"
        yield "data: [DONE]\n\n"

    except Exception as e:
        logger.error(f"Error during LangGraph streaming execution for session {session_id}: {str(e)}")
        err_msg = json.dumps({"type": "error", "content": "An error occurred while processing your query."})
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
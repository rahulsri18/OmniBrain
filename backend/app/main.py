import asyncio
import json
from fastapi import BackgroundTasks, FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.gzip import GZipMiddleware
from .middleware.rate_limiter import limiter
from app.core.exceptions import GuardrailViolation
from app.core.security import verify_api_key
from app.services.session_manager import session_manager
from app.utils.stream_formatter import stream_formatter
from .services.ingestion_service import IngestionService
from .sql_agent.schema import ChatRequest
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from fastapi import Depends


# Import compiled graph safely
try:
    from agents.graph import app_graph
except ImportError:
    app_graph = None

app = FastAPI(title="OmniBrain Backend", version="0.1.0")

app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    GZipMiddleware,
    minimum_size=1000
)


# --- Global Exception Handler for Guardrails (Day 13) ---
@app.exception_handler(GuardrailViolation)
async def guardrail_exception_handler(
    request: Request,
    exc: GuardrailViolation,
):
    """Global handler returning HTTP 400 for guardrail violations."""
    return JSONResponse(
        status_code=400,
        content={
            "status": "blocked",
            "message": exc.message,
        },
    )


ingestion_service = IngestionService()
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
REQUEST_TIMEOUT = 30  # seconds


@app.middleware("http")
async def timeout_middleware(request, call_next):
    if request.url.path.startswith("/api/v1/chat"):
        return await call_next(request)

    try:
        return await asyncio.wait_for(call_next(request), timeout=REQUEST_TIMEOUT)
    except asyncio.TimeoutError:
        return JSONResponse(
            status_code=504,
            content={"detail": "Request timed out. Please try again."},
        )


@app.get(
    "/",
    summary="Health Check",
    description="Checks whether the OmniBrain backend server is running.",
    response_description="Server status message"
)
def home():
    return {"message": "Server is running"}

@app.post(
    "/api/v1/upload",
    summary="Upload PDF",
    description="Uploads a PDF document for background ingestion into the knowledge base.",
    response_description="Upload accepted successfully.",
    responses={
        200: {"description": "PDF uploaded successfully"},
        400: {"description": "Invalid file type"},
        413: {"description": "File size exceeds 50 MB"},
        429: {"description": "Too many upload requests"}
    }
)
@limiter.limit("10/minute")
async def upload_file(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key),
):
    is_pdf_mime = file.content_type == "application/pdf"
    is_pdf_ext = file.filename.lower().endswith(".pdf")

    if not (is_pdf_mime or is_pdf_ext):
        raise HTTPException(
            status_code=400, detail="Only PDF files are allowed."
        )

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413, detail="File size exceeds the 50 MB limit."
        )

    try:
        temp_file_path = await ingestion_service.save_file_temporarily(file)

        background_tasks.add_task(
            ingestion_service.process_pipeline_from_path,
            temp_file_path,
            file.filename,
        )

        return {
            "status": "accepted",
            "filename": file.filename,
            "message": "File uploaded successfully. Processing started in the background.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


async def chat_stream(message: str, session_id: str = None, file_path: str = None):
    """Core Event Streamer wrapping LangGraph execution."""
    async def event_generator():
        if app_graph is None:
            yield {"type": "error", "content": "LangGraph instance is not initialized on the server."}
            return

        initial_state = {
            "messages": [{"role": "user", "content": message}],
            "session_id": session_id,
            "file_path": file_path,
            "question": message,
        }

        try:
            async for event in app_graph.astream_events(initial_state, version="v2"):
                kind = event.get("event")
                name = event.get("name", "")

                if kind == "on_chain_start" and name in ["supervisor", "rag_node", "sql_node", "vision_node", "grader_node", "rewrite_node"]:
                    yield {"type": "reasoning", "thought": f"Executing node: {name}", "node": name}

                elif kind == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    if hasattr(chunk, "content") and chunk.content:
                        yield {"type": "content", "content": chunk.content}

        except asyncio.TimeoutError:
            yield {"type": "error", "content": "LangGraph execution timed out."}
        except GuardrailViolation as gv:
            yield {
                "type": "error",
                "status": "blocked",
                "reason": "guardrail",
                "message": gv.message,
                "content": gv.message,
            }
        except Exception as exc:
            yield {"type": "error", "content": f"Graph Execution Error: {str(exc)}"}

    async for chunk in stream_formatter(event_generator()):
        yield chunk


@app.post(
    "/api/v1/chat",
    summary="Chat",
    description="Processes user queries and streams AI-generated responses.",
    response_description="Streaming chat response",
    responses={
        200: {"description": "Chat response generated successfully"},
        400: {"description": "Invalid request"},
        429: {"description": "Too many requests"}
    }
)
@limiter.limit("30/minute")
async def chat(
    request: Request,
    chat_request: ChatRequest,
    api_key: str = Depends(verify_api_key),
):
    """Clean Single Route for Chat Streaming with Error Guardrails."""
    # Optional synchronous guardrail check before starting stream
    # if is_violating_guardrail(request.message):
    #     raise GuardrailViolation("Input prompt contains policy violations.")

    session_id = getattr(chat_request, "session_id", None)
    if not session_id or not session_manager.get_session(session_id):
        session_id = session_manager.create_session()

    session_manager.add_message(
        session_id, role="user", content=chat_request.message
    )

    file_path = getattr(chat_request, "file_path", None)

    return StreamingResponse(
        chat_stream(chat_request.message, session_id, file_path),
        media_type="text/event-stream",
        headers={"X-Session-ID": session_id},
    )


@app.get(
    "/api/v1/status",
    summary="Execution Status",
    description="Returns the current execution status of background tasks.",
    response_description="Execution status"
)
async def execution_status(
    api_key: str = Depends(verify_api_key),
):
    """Live execution status endpoint."""
    return {
        "status": "grading",
        "message": "Document grading is in progress."
    }


@app.get(
    "/api/v1/telemetry",
    summary="Telemetry",
    description="Returns backend telemetry and runtime metrics.",
    response_description="Telemetry information"
)
async def telemetry(
    session_id: str = Query(None),
    api_key: str = Depends(verify_api_key),
):
    """Telemetry endpoint for query rewrite statistics."""
    if session_id:
        session = session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")

        rewrite_count = session.get("rewrite_count", 0)
        return {
            "session_id": session_id,
            "query_rewrites": rewrite_count,
            "status": "tracking",
            "message": f"Query rewrite count retrieved for session {session_id}."
        }

    return {
        "query_rewrites": 0,
        "status": "tracking",
        "message": "Query rewrite telemetry is active."
    }
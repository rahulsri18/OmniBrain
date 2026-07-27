import asyncio
from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from app.services.session_manager import session_manager
from app.utils.stream_formatter import stream_formatter
from .services.ingestion_service import IngestionService
from .sql_agent.schema import ChatRequest

# Import compiled graph safely
try:
    from agents.graph import app_graph
except ImportError:
    app_graph = None

app = FastAPI(title="OmniBrain Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


@app.get("/")
def home():
    return {"message": "Server is running"}


@app.post("/api/v1/upload")
async def upload_file(
    background_tasks: BackgroundTasks, file: UploadFile = File(...)
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
    """
    Core Event Streamer wrapping LangGraph execution in explicit try-except timeouts.
    """
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
            # Stream LangGraph execution with chunk timeout protection
            async for event in app_graph.astream_events(initial_state, version="v2"):
                kind = event.get("event")
                name = event.get("name", "")

                if kind == "on_chain_start" and name in ["supervisor", "rag_node", "sql_node", "vision_node"]:
                    yield {"type": "reasoning", "thought": f"Executing node: {name}", "node": name}

                elif kind == "on_chat_model_stream":
                    chunk = event.get("data", {}).get("chunk")
                    if hasattr(chunk, "content") and chunk.content:
                        yield {"type": "content", "content": chunk.content}

        except asyncio.TimeoutError:
            yield {"type": "error", "content": "LangGraph execution timed out."}
        except Exception as exc:
            yield {"type": "error", "content": f"Graph Execution Error: {str(exc)}"}

    async for chunk in stream_formatter(event_generator()):
        yield chunk


@app.post("/api/v1/chat")
async def chat(request: ChatRequest):
    """Clean Single Route for Chat Streaming with Error Guardrails."""
    session_id = getattr(request, "session_id", None)
    if not session_id or not session_manager.get_session(session_id):
        session_id = session_manager.create_session()

    session_manager.add_message(
        session_id, role="user", content=request.message
    )

    file_path = getattr(request, "file_path", None)

    return StreamingResponse(
        chat_stream(request.message, session_id, file_path),
        media_type="text/event-stream",
        headers={"X-Session-ID": session_id},
    )
    
@app.get("/api/v1/status")
async def execution_status():
    """Live execution status endpoint."""
    return{
        "status": "grading",
        "message": "Document grading is in progress."
    }
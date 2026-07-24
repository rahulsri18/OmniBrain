import asyncio
from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
from app.services.session_manager import session_manager
from app.utils.stream_formatter import stream_formatter
from .services.ingestion_service import IngestionService
from .sql_agent.schema import ChatRequest


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
REQUEST_TIMEOUT = 30 #seconds


@app.middleware("http")
async def timeout_middleware (request, call_next):
    try:
        response = await asyncio.wait_for(call_next(request), timeout=REQUEST_TIMEOUT)
        return response
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
    # MIME / Extension validation
    is_pdf_mime = file.content_type == "application/pdf"
    is_pdf_ext = file.filename.lower().endswith(".pdf")

    if not (is_pdf_mime or is_pdf_ext):
        raise HTTPException(
            status_code=400, detail="Only PDF files are allowed."
        )

    # File size validation
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


async def chat_stream(message: str, session_id: str = None):
    words = [
        "Hello!",
        "This",
        "is",
        "a",
        "streaming",
        "response",
        "from",
        "OmniBrain.",
    ]

    async def event_stream():
        # Stream mock words (Will be replaced by LangGraph stream in next milestone)
        for word in words:
            yield {"type": "assistant", "content": word}
            await asyncio.sleep(0.15)

    async for chunk in stream_formatter(event_stream()):
        yield chunk


@app.post("/api/v1/chat")
async def chat(request: ChatRequest):
    """Clean Single Route for Chat Streaming with Session Management."""
    session_id = request.session_id
    if not session_id or not session_manager.get_session(session_id):
        session_id = session_manager.create_session()

    # Save user message to session memory
    session_manager.add_message(
        session_id, role="user", content=request.message
    )

    return StreamingResponse(
        chat_stream(request.message, session_id),
        media_type="text/event-stream",
        headers={"X-Session-ID": session_id},
    )
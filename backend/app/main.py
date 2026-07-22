from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel 
import asyncio
from fastapi.middleware.cors import CORSMiddleware
from .services.ingestion_service import IngestionService
from .sql_agent.schema import ChatRequest
from app.utils.stream_formatter import stream_formatter

app = FastAPI(
    title="OmniBrain Backend",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ingestion_service = IngestionService()
MAX_FILE_SIZE = 50 * 1024 * 1024  


@app.get("/")
def home():
    return {"message": "Server is running"}


@app.post("/api/v1/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    # डबल वैलिडेशन
    is_pdf_mime = file.content_type == "application/pdf"
    is_pdf_ext = file.filename.lower().endswith(".pdf")

    if not (is_pdf_mime or is_pdf_ext):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed."
        )
    # File size validation (500 MB)
    file.file.seek(0, 2)              # Move to end of file
    file_size = file.file.tell()      # Get file size in bytes
    file.file.seek(0)                 # Move back to beginning

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
        status_code=413,
        detail="File size exceeds the 50 MB limit."
    )
    try:
        # 🔥 फिक्स: फ़ाइल को रिक्वेस्ट खत्म होने से पहले तुरंत डिस्क पर सेव कर लो
        temp_file_path = await ingestion_service.save_file_temporarily(file)
        
        # 🔥 अब बैकग्राउंड टास्क को 'file' ऑब्जेक्ट नहीं, बल्कि 'file_path' भेजो
        background_tasks.add_task(
            ingestion_service.process_pipeline_from_path,  # तुम्हारी सर्विस का नया मेथड
            temp_file_path,
            file.filename
        )

        return {
            "status": "accepted",
            "filename": file.filename,
            "message": "File uploaded successfully. Processing started in the background."
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
        "OmniBrain."
    ]

    async def event_stream():
        for word in words:
            yield {"type": "assistant", "content": word}
            await asyncio.sleep(0.3)

    async for chunk in stream_formatter(event_stream()):
        yield chunk


@app.post("/api/v1/chat")
async def chat(request: ChatRequest):
    return StreamingResponse(
        chat_stream(request.message),
        media_type="text/event-stream"
    )
from app.services.session_manager import session_manager

@app.post("/api/v1/chat")
async def chat(request: ChatRequest):
    # 1. सेशन आईडी चेक या क्रिएट करो
    session_id = request.session_id
    if not session_id or not session_manager.get_session(session_id):
        session_id = session_manager.create_session()

    # 2. यूज़र मैसेज हिस्ट्री में जोड़ो
    session_manager.add_message(session_id, role="user", content=request.message)

    # 3. स्ट्रीमिंग रिस्पॉन्स में सेशन आईडी रिफ्लेक्ट करो
    return StreamingResponse(
        chat_stream(request.message, session_id),
        media_type="text/event-stream",
        headers={"X-Session-ID": session_id}
    )
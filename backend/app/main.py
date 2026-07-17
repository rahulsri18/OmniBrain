from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="OmniBrain Backend",
    version="0.1.0"
)

# CORS को वापस सही तरीके से सेट करें (वरना फ्रंटएंड कनेक्ट नहीं होगा)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    # Welcome to OmniBrain Backend!
    return {"message": "Server is running"}


@app.post("/api/v1/upload")
async def upload_file(file: UploadFile = File(...)):
    # डबल वैलिडेशन: Content Type और File Extension दोनों चेक करें
    is_pdf_mime = file.content_type == "application/pdf"
    is_pdf_ext = file.filename.lower().endswith(".pdf")

    if not (is_pdf_mime or is_pdf_ext):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed."
        )

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "message": "PDF uploaded successfully."
    }
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

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

@app.get("/")
def home():
    # Welcome to OmniBrain Backend!
    return {"message": "Server is running"}

@app.post("/api/v1/upload")
async def upload_file(file: UploadFile = File(...)):

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed."
        )

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "message": "PDF uploaded successfully."
    }
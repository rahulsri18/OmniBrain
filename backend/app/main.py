from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
# 👈 अपनी नई सर्विस को इम्पोर्ट करो
from app.services.ingestion_service import IngestionService  

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

# सर्विस क्लास को इनिशियलाइज़ किया
ingestion_service = IngestionService()


@app.get("/")
def home():
    return {"message": "Server is running"}


@app.post("/api/v1/upload")
async def upload_file(file: UploadFile = File(...)):
    # डबल वैलिडेशन (M5 का कोड)
    is_pdf_mime = file.content_type == "application/pdf"
    is_pdf_ext = file.filename.lower().endswith(".pdf")

    if not (is_pdf_mime or is_pdf_ext):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed."
        )

    # 👈 तुम्हारी सर्विस पाइपलाइन यहाँ ट्रिगर होगी
    result = await ingestion_service.process_pipeline(file)
    
    if result["status"] == "failed":
        raise HTTPException(status_code=500, detail=result["error"])

    return result
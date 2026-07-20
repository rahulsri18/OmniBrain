# backend/app/services/ingestion_service.py
import os
import shutil
import traceback
from fastapi import UploadFile
from app.logger import logger

# M2 की फाइनल हो चुकी असली पाइपलाइन को इम्पोर्ट कर रहे हैं
from app.ingestion.ingestion import IngestionPipeline


class IngestionService:
    def __init__(self):
        # टेम्परेरी फ़ाइलें सेव करने के लिए डायरेक्टरी
        self.upload_dir = "temp_uploads"
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)
            logger.info(f"Created temp upload directory at: {self.upload_dir}")
            
        # M2 की पाइपलाइन को इनिशियलाइज़ किया
        self.pipeline = IngestionPipeline()

    async def save_file_temporarily(self, file: UploadFile) -> str:
        """
        FastAPI के क्लोज़ होने से पहले फ़ाइल को तुरंत डिस्क पर सुरक्षित सेव करता है।
        """
        file_path = os.path.join(self.upload_dir, file.filename)
        logger.info(f"Saving {file.filename} temporarily to disk...")
        
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            return file_path
        except Exception as e:
            logger.error(f"Failed to save temp file: {e}")
            raise e

    def process_pipeline_from_path(self, temp_path: str, original_filename: str):
        """
        🚀 ⚡ डे 4 बैकग्राउंड टास्क मेथड:
        FastAPI इसे बैकग्राउंड में चलाएगा। यह सीधे पाथ से फ़ाइल उठाकर 
        M2 की पूरी पार्सिंग, चंकिंग और Qdrant पाइपलाइन को रन करता है।
        """
        try:
            logger.info(f"[Background] Starting heavy ingestion pipeline for: {original_filename}")
            
            # 🔥 M2 की असली प्रोडक्शन पाइपलाइन यहाँ ट्रिगर होगी!
            # यह फ़ाइल को पार्स करेगी, चंक करेगी, SentenceTransformers से 
            # 384-dim के वेक्टर्स बनाकर Qdrant में सुरक्षित डाल देगी।
            self.pipeline.ingest_pdf(temp_path)
            
            logger.info(f"[Background] Ingestion successful for: {original_filename}")

        except Exception as e:
            traceback.print_exc()
            logger.exception(
        f"[Background] Critical error in ingestion pipeline for {original_filename}"
        )
            
        finally:
            # क्लीनअप: काम होने के बाद (या एरर आने पर भी) टेम्परेरी फाइल डिलीट करो
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
                logger.info(f"[Background] Cleaned up temporary file from disk: {temp_path}")
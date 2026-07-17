# backend/app/services/ingestion_service.py
import os
import shutil
from fastapi import UploadFile
from app.logger import logger
# 🚀 M2 के मौजूदा utils फोल्डर से क्लास इम्पोर्ट कर रहे हैं
from app.utils.pdf_parser import PDFParser 

class IngestionService:
    def __init__(self):
        self.upload_dir = "temp_uploads"
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)

    async def save_file_temporarily(self, file: UploadFile) -> str:
        """फ़ाइल को डिस्क पर टेम्परेरी सेव करता है।"""
        file_path = os.path.join(self.upload_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return file_path

    async def process_pipeline(self, file: UploadFile) -> dict:
        """मुख्य पाइपライン: सेव -> पार्स (M2 Code) -> क्लीनअप।"""
        temp_path = None
        try:
            temp_path = await self.save_file_temporarily(file)
            
            logger.info(f"Running M2's PDFParser from utils for {file.filename}")
            
            # 🚀 M2 की क्लास को इनिशियलाइज़ और कॉल करना
            parser = PDFParser(temp_path)
            extracted_text = parser.extract_text()
            metadata = parser.get_metadata()

            # चंकिंग और वेक्टराइजेशन अभी मॉक रहेगा
            chunks_count = len(extracted_text) // 400 + 1 

            return {
                "status": "success",
                "filename": file.filename,
                "total_pages": metadata["total_pages"],
                "chunks_ingested": chunks_count,
                "message": "PDF uploaded and parsed successfully using M2's utils parser!"
            }
        except Exception as e:
            logger.error(f"Error in service layer: {e}")
            return {"status": "failed", "error": str(e)}
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
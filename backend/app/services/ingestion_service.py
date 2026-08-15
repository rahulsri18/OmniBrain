# backend/app/services/ingestion_service.py
import os
import shutil
import traceback
from fastapi import UploadFile
from ..logger import logger

from ..ingestion.ingestion import IngestionPipeline


class IngestionService:
    def __init__(self):
        self.upload_dir = "temp_uploads"
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)
            logger.info(f"Created temp upload directory at: {self.upload_dir}")
            
        self.pipeline = IngestionPipeline()

    async def save_file_temporarily(self, file: UploadFile) -> str:
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
        try:
            logger.info(f"[Background] Starting heavy ingestion pipeline for: {original_filename}")
            
            self.pipeline.ingest_pdf(temp_path)
            
            logger.info(f"[Background] Ingestion successful for: {original_filename}")

        except Exception as e:
            traceback.print_exc()
            logger.exception(
        f"[Background] Critical error in ingestion pipeline for {original_filename}"
        )
            
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
                logger.info(f"[Background] Cleaned up temporary file from disk: {temp_path}")
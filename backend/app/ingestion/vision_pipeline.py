import os
import re
import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from app.vectordb.qdrant_client import QdrantDB  # M2 का डेटाबेस स्क्रिप्ट
from app.logger import logger

class VisionIngestionPipeline:

    """
    CLIP मॉडल से इमेज एम्बेडिंग्स जनरेट करने और 
    उन्हें Qdrant में स्टोर करने की विज़न पाइपलाइन (Day 3 & Day 4)।
    """

    def __init__(self):
        logger.info("Loading HuggingFace CLIP Model (openai/clip-vit-base-patch32)...")
        # Day 3: CLIP Model और Processor लोड करें
        self.model_name = "openai/clip-vit-base-patch32"
        self.processor = CLIPProcessor.from_pretrained(self.model_name)
        self.model = CLIPModel.from_pretrained(self.model_name)
        
        # CPU/GPU ऑटोडिटेक्ट
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        
        # Day 4: M2 का डेटाबेस क्लाइंट और विज़न के लिए 512 साइज़ लॉकिंग
        self.db = QdrantDB()
        self.collection_name = "omnibrain_vision"
        self.vector_size = 512  # CLIP-ViT-B/32 का विज़न आउटपुट साइज़
        
        # पक्का करें कि विज़न के लिए Qdrant कलेक्शन तैयार है
        self._ensure_vision_collection()

    
    def _ensure_vision_collection(self):
        """विज़न वेक्टर्स के लिए अलग कलेक्शन बनाना ताकि साइज कॉन्फ्लिक्ट न हो"""
        try:
            # अगर M2 की QdrantDB क्लास में create_collection मेथड है:
            self.db.client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config={"size": self.vector_size, "distance": "Cosine"}
            )
            logger.info(f"Qdrant Vision collection '{self.collection_name}' initialized with size {self.vector_size}.")
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant Vision collection: {e}")

    

    def generate_image_embedding(self, image_path: str) -> list:
        """
        Day 3: CLIP मॉडल का उपयोग करके इमेज को 512-डायमेंशन वेक्टर में बदलता है।
        """
        try:
            image = Image.open(image_path).convert("RGB")
            inputs = self.processor(images=image, return_tensors="pt").to(self.device)
            
            with torch.no_grad():
                image_features = self.model.get_image_features(**inputs)
                
            # नॉर्मलाइज़ करें और लिस्ट में बदलें
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            embedding = image_features.cpu().numpy()[0].tolist()
            return embedding
        except Exception as e:
            logger.error(f"Error generating CLIP embedding for {image_path}: {str(e)}")
            return []
    
    
    def _extract_page_number(self, image_path: str) -> int | None:
        """Infer the source PDF page from the extracted image filename when available."""
        match = re.search(r"_p(\d+)_img\d+", os.path.basename(image_path))
        if not match:
            return None

        try:
            return int(match.group(1))
        except ValueError:
            return None
    

    def ingest_extracted_images(self, image_paths: list, original_pdf_name: str):
        """
        Day 4: इमेज वेक्टर्स और मेटाडेटा को M2 के Qdrant स्क्रिप्ट के ज़रिए डेटाबेस में स्टोर करना।
        """
        if not image_paths:
            logger.info("No images to ingest into Qdrant.")
            return

        embeddings = []
        valid_paths = []
        metadata = []


        # 1. सभी इमेजेस के वेक्टर्स और पेलोड तैयार करें
        for idx, img_path in enumerate(image_paths):
            vector = self.generate_image_embedding(img_path)
            if vector:
                page_number = self._extract_page_number(img_path)
                embeddings.append(vector)
                valid_paths.append(img_path)
                payload = {
                    "file_name": original_pdf_name,
                    "asset_path": img_path,
                    "asset_index": idx + 1,
                    "type": "chart_or_image"
                }

                if page_number is not None:
                    payload["page"] = page_number
                    payload["page_number"] = page_number

                metadata.append(payload)

        if not embeddings:
            return

        # 2. Qdrant में इंसर्ट करें 
        # (नोट: यहाँ M2 के insert_vectors को कॉल करते समय विज़न का कलेक्शन नेम पास कर रहे हैं)
        try:
            logger.info(f"Uploading {len(embeddings)} image vectors to Qdrant...")
            
            # अगर M2 की insert_vectors क्लास डायरेक्ट कलेक्शन नेम एक्सेप्ट करती है:
            self.db.insert_vectors(
                    chunks=valid_paths,  # Chunks पैरामीटर में इमेज पाथ पास कर रहे हैं
                    embeddings=embeddings,
                    metadata=metadata,
                    collection_name=self.collection_name # अगर M2 ने सपोर्ट दिया है
                )
            logger.info("Vision vectors ingestion completed successfully!")
        except Exception as e:
            logger.error(f"Failed storing vision vectors in Qdrant: {e}")

        
import os
import fitz  # PyMuPDF
from io import BytesIO
from PIL import Image
from ..logger import logger

class PDFVisionExtractor:
    def __init__(self, output_dir: str = "extracted_assets", min_width: int = 150, min_height: int = 150, min_size_bytes: int = 5000):
        self.output_dir = output_dir
        self.min_width = min_width
        self.min_height = min_height
        self.min_size_bytes = min_size_bytes
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def is_high_quality(self, img_bytes: bytes, width: int, height: int) -> bool:
        if width < self.min_width or height < self.min_height:
            return False
            
        if len(img_bytes) < self.min_size_bytes:
            return False
            
        return True

    def extract_images_from_pdf(self, pdf_path: str) -> list:
        extracted_paths = []
        filename = os.path.splitext(os.path.basename(pdf_path))[0]
        
        try:
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images(full=True)
                
                for img_idx, img_info in enumerate(image_list):
                    xref = img_info[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    
                    img = Image.open(BytesIO(image_bytes))
                    width, height = img.size
                    
                    if not self.is_high_quality(image_bytes, width, height):
                        logger.info(f"Filtered out low-quality image: Page {page_num+1}, Index {img_idx} ({width}x{height})")
                        continue
                        
                    img_name = f"{filename}_p{page_num+1}_img{img_idx+1}.{image_ext}"
                    save_path = os.path.join(self.output_dir, img_name)
                    
                    with open(save_path, "wb") as f:
                        f.write(image_bytes)
                        
                    extracted_paths.append(save_path)
                    logger.info(f"Successfully extracted high-quality image: {img_name}")
                    
            doc.close()
        except Exception as e:
            logger.error(f"Error extracting images from PDF {pdf_path}: {str(e)}")
            
        return extracted_paths
        
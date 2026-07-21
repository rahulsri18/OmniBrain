import os
import fitz  # PyMuPDF
from io import BytesIO
from PIL import Image
from ..logger import logger

class PDFVisionExtractor:
    """
    PDF दस्तावेज़ों से इमेज और चार्ट्स एक्सट्रैक्ट करने और 
    लो-क्वालिटी एसेट्स को फ़िल्टर करने का मॉड्यूल (Day 2 & Day 5)।
    """
    def __init__(self, output_dir: str = "extracted_assets", min_width: int = 150, min_height: int = 150, min_size_bytes: int = 5000):
        self.output_dir = output_dir
        self.min_width = min_width
        self.min_height = min_height
        self.min_size_bytes = min_size_bytes
        
        # Day 1: स्टोरेज डायरेक्टरी बनाएँ
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def is_high_quality(self, img_bytes: bytes, width: int, height: int) -> bool:
        """
        Day 5: लो-क्वालिटी इमेज, छोटे आइकॉन या खाली स्पेस को फ़िल्टर करने का लॉजिक।
        """
        # 1. डायमेंशन चेक (Resolution Check)
        if width < self.min_width or height < self.min_height:
            return False
            
        # 2. फ़ाइल साइज़ चेक (बाइट्स में)
        if len(img_bytes) < self.min_size_bytes:
            return False
            
        return True

    def extract_images_from_pdf(self, pdf_path: str) -> list:
        """
        Day 2: PDF के हर पेज से इमेज एक्सट्रैक्ट करके डिस्क पर सेव करता है।
        """
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
                    
                    # PIL Image ऑब्जेक्ट बनाएँ ताकि विड्थ और हाइट मिल सके
                    img = Image.open(BytesIO(image_bytes))
                    width, height = img.size
                    
                    # 🔥 Day 5: लो-क्वालिटी फ़िल्टर कंडीशन
                    if not self.is_high_quality(image_bytes, width, height):
                        logger.info(f"Filtered out low-quality image: Page {page_num+1}, Index {img_idx} ({width}x{height})")
                        continue
                        
                    # सेफ इमेज नाम और पाथ तैयार करें
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
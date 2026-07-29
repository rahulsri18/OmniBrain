"""
vision_prompts.py

Day 6 - M4 Task:
Prompt engineering architecture and input image-formatting class for the Vision Sub-Agent.
Handles image encoding, formatting payloads, and structuring vision system prompts.
"""

import base64
import os
from io import BytesIO
from typing import List, Dict, Any, Union, Optional
from PIL import Image
from app.logger import logger


# ==========================================
# 1. Vision Sub-Agent System Prompts
# ==========================================

VISION_SYSTEM_PROMPT = """You are OmniBrain's specialized Vision Sub-Agent. Your task is to analyze images, charts, diagrams, tables, and visual technical documentation extracted from documents.

### Instructions:
1. **Accuracy First:** Extract data, figures, and trends directly from the provided images without hallucinations.
2. **Contextual Analysis:** Explain charts, graphs, flowcharts, or architecture diagrams clearly with bullet points.
3. **Structured Output:**
   - **Summary:** Brief description of what the visual represents.
   - **Key Findings / Data Points:** Specific values, axes labels, or key structural elements.
   - **Relevance:** How this visual relates to the user's query.
4. **Unclear Images:** If the image is blurry, corrupted, or lacks readable information, state that clearly.
"""

VISION_ROUTER_PROMPT = """You are analyzing visual queries. Determine if the user's prompt requires:
1. Visual data extraction (e.g., reading a chart, graph, or architectural diagram).
2. Image-to-Text OCR / Text extraction.
3. Multi-modal comparison (comparing text context with image content).
"""


# ==========================================
# 2. Image Formatting Class
# ==========================================

class ImageFormatter:
    """
    Handles image conversion, resizing for token-optimization, 
    and formatting into vision-model compatible JSON payloads.
    """

    @staticmethod
    def encode_image_to_base64(image_input: Union[str, bytes, Image.Image]) -> Optional[str]:
        """
        Convert file path, raw bytes, or PIL Image into Base64 string.
        """
        try:
            if isinstance(image_input, str):
                if not os.path.exists(image_input):
                    logger.error(f"Image path does not exist: {image_input}")
                    return None
                with open(image_input, "rb") as img_file:
                    return base64.b64encode(img_file.read()).decode("utf-8")

            elif isinstance(image_input, bytes):
                return base64.b64encode(image_input).decode("utf-8")

            elif isinstance(image_input, Image.Image):
                buffered = BytesIO()
                # Maintain original format or default to PNG
                img_format = image_input.format if image_input.format else "PNG"
                image_input.save(buffered, format=img_format)
                return base64.b64encode(buffered.getvalue()).decode("utf-8")

            else:
                logger.error(f"Unsupported image input type: {type(image_input)}")
                return None

        except Exception as e:
            logger.error(f"Error encoding image to base64: {str(e)}")
            return None

    @staticmethod
    def get_mime_type(image_path: str) -> str:
        """
        Infer MIME type based on file extension.
        """
        ext = os.path.splitext(image_path)[1].lower()
        if ext in [".jpg", ".jpeg"]:
            return "image/jpeg"
        elif ext == ".png":
            return "image/png"
        elif ext == ".webp":
            return "image/webp"
        else:
            return "image/png"

    def format_vision_payload(
        self,
        user_prompt: str,
        image_inputs: List[Union[str, bytes, Image.Image]],
        system_prompt: str = VISION_SYSTEM_PROMPT
    ) -> Dict[str, Any]:
        """
        Formats prompt and images into a standardized LangChain / OpenAI / Gemini style multi-modal payload.
        """
        formatted_images = []

        for idx, img_input in enumerate(image_inputs):
            b64_str = self.encode_image_to_base64(img_input)
            if not b64_str:
                logger.warning(f"Skipping unprocessable image at index {idx}")
                continue

            mime_type = "image/png"
            if isinstance(img_input, str):
                mime_type = self.get_mime_type(img_input)

            formatted_images.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{mime_type};base64,{b64_str}"
                }
            })

        # Build combined content array
        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    *formatted_images
                ]
            }
        ]

        return {
            "messages": messages,
            "processed_image_count": len(formatted_images)
        }


# Global instance for quick access across sub-agents
image_formatter = ImageFormatter()

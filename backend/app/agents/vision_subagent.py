# app/agents/vision_subagent.py

import json
import logging
from typing import Dict, Any
# pyrefly: ignore [missing-import]
from app.agents.vision_prompt import TUNED_VISION_SUBAGENT_PROMPT
from app.schemas.vision_schema import VisionAnalysisOutput

logger = logging.getLogger("omnibrain.vision")

async def analyze_visual_chunk_tuned(client, base64_image: str) -> Dict[str, Any]:
    """
    Tuned Vision Sub-Agent caller with low-temperature and strict max-token limit.
    """
    try:
        response = await client.chat.completions.create(
            model="gpt-4o",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": TUNED_VISION_SUBAGENT_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract visual facts:"},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        }
                    ]
                }
            ],
            temperature=0.0,    # Absolute zero temperature for maximum accuracy
            max_tokens=500      # Hard token cap to prevent verbose responses
        )
        
        raw_json = response.choices[0].message.content
        parsed = json.loads(raw_json)
        
        # Validate against Pydantic Schema
        return VisionAnalysisOutput(**parsed).model_dump()

    except Exception as e:
        logger.error(f"Tuned Vision Sub-Agent Exception: {str(e)}")
        return {
            "image_type": "unknown",
            "summary": "Unparseable visual chunk.",
            "confidence_score": 0.0,
            "raw_markdown_representation": ""
        }
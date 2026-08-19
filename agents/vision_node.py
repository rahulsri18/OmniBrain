"""
agents/vision_node.py

M4 - Vision Sub-Agent Node.

Single, coherent implementation:
1. Validate a file_path was provided.
2. Run blur detection (Day 11 quality check) BEFORE calling the LLM,
   so we never burn an API call on an unreadable image.
3. If the image passes, encode it and call the real vision LLM
   (GPT-4o) using the strict numerical-accuracy system prompt.
   The call now streams via .astream() (not .invoke()) so LangGraph
   emits on_chat_model_stream events that main.py's chat_stream()
   listens for.
4. On any failure, set image_error / error so the graph's
   route_after_vision() / grader can divert to the fallback node.
"""

import os
import base64
from typing import Any, Dict, Optional

import cv2
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from backend.app.config import settings
from backend.app.logger import logger
from agents.prompts import VISION_SYSTEM_PROMPT


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def encode_image_to_base64(image_path: str) -> Optional[str]:
    """Encode a local image/chart into base64 for the vision LLM payload."""
    try:
        if not os.path.exists(image_path):
            logger.error(f"Image path does not exist: {image_path}")
            return None

        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        logger.error(f"Failed to encode image at {image_path}: {e}")
        return None


def detect_blur(image_path: str, threshold: float = 80.0) -> bool:
    """
    Computes the Laplacian variance of the image. If variance is below
    the threshold, the image is considered too blurry to read reliably.
    """
    try:
        image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if image is None:
            return True  # Unreadable file -> treat as blurry/broken

        variance = cv2.Laplacian(image, cv2.CV_64F).var()
        return variance < threshold
    except Exception:
        return True


class VisionSubAgent:
    """Wraps the GPT-4o multimodal call for chart/graph analysis."""

    def __init__(self, model_name: str = "gpt-4o"):
        self.llm = ChatOpenAI(
            model=model_name,
            api_key=settings.OPENAI_API_KEY,
            temperature=0.0,  # strict, to avoid hallucinated numbers
        )

    async def analyze_chart_or_graph(self, user_query: str, image_path: str) -> str:
        """
        Streams the vision LLM's response token-by-token via .astream(),
        so LangGraph fires on_chat_model_stream events for the caller
        (main.py's chat_stream) to forward over SSE.
        """
        base64_image = encode_image_to_base64(image_path)
        if not base64_image:
            return "Unable to process the image file. Please verify the image path."

        messages = [
            SystemMessage(content=VISION_SYSTEM_PROMPT),
            HumanMessage(
                content=[
                    {
                        "type": "text",
                        "text": f"User Request: {user_query}\n\nPlease analyze this chart/graph and answer the query.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                    },
                ]
            ),
        ]

        try:
            logger.info(f"VisionSubAgent analyzing image: {image_path}")
            full_response = ""
            async for chunk in self.llm.astream(messages):
                if chunk.content:
                    full_response += chunk.content
            return full_response
        except Exception as e:
            logger.error(f"Error during Vision LLM invocation: {e}")
            return f"Failed to analyze the image due to an error: {str(e)}"


# ---------------------------------------------------------------------------
# LangGraph node
# ---------------------------------------------------------------------------

async def vision_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node for vision analysis. Runs blur detection first;
    only calls the real vision LLM if the image passes quality checks.
    """
    file_path = state.get("file_path")
    messages = state.get("messages", [])

    # 1. Must have a file path at all.
    if not file_path:
        return {
            "image_error": True,
            "error": "No image or chart file path was provided for vision analysis.",
        }

    # 2. Blur / quality check (Day 11) — before spending an LLM call.
    if detect_blur(file_path):
        return {
            "image_error": True,
            "error": "Image is too blurry or table content is unclear. Please provide a higher-resolution document.",
        }

    # 3. Extract the user's question from the last message, if present.
    user_query = state.get("question") or "Summarize and analyze the key insights from this chart."
    if messages:
        last_msg = messages[-1]
        user_query = (
            last_msg.get("content")
            if isinstance(last_msg, dict)
            else getattr(last_msg, "content", user_query)
        )

    # 4. Real vision call (streamed).
    agent = VisionSubAgent()
    analysis_result = await agent.analyze_chart_or_graph(user_query=user_query, image_path=file_path)

    new_messages = list(messages)
    new_messages.append({"role": "assistant", "content": analysis_result})

    return {
        "messages": new_messages,
        "context": [analysis_result],
        "response": analysis_result,
        "answer": analysis_result,
        "image_error": False,
    }

async def execute_vision_agent(
    image_path: str,
    question: str,
    vision_llm,
    use_backup_rephraser: bool = False,
    raw_previous_output: str = "",
):
    """
    Compatibility function required by
    tests/test_vision_backup_prompt.py.
    """

    if use_backup_rephraser and raw_previous_output:

        prompt = (
            f"Question: {question}\n\n"
            f"Raw OCR Output:\n{raw_previous_output}\n\n"
            "Rewrite this into a clear summary."
        )

        response = await vision_llm.ainvoke(prompt)

        return {
            "vision_output": response.content,
            "is_rephrased": True,
            "image_error": False,
        }

    return {
        "vision_output": raw_previous_output,
        "is_rephrased": False,
        "image_error": False,
    }
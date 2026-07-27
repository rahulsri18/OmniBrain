"""
vision_node.py

M4 - Vision Sub-Agent Node
Reads mixed PDF charts, graphs, and images, and generates text analysis
using OpenAI Vision LLM. Integrated as a node in LangGraph workflow.
"""

import os
import base64
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from backend.app.config import Settings
from backend.app.logger import logger

settings = Settings()


def encode_image_to_base64(image_path: str) -> Optional[str]:
    """Helper function to encode a local image/chart into base64 format."""
    try:
        if not os.path.exists(image_path):
            logger.error(f"Image path does not exist: {image_path}")
            return None
            
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        logger.error(f"Failed to encode image at {image_path}: {e}")
        return None


class VisionSubAgent:
    def __init__(self, model_name: str = "gpt-4o"):
        """Initialize the Vision Agent with GPT-4o / Multimodal model."""
        self.llm = ChatOpenAI(
            model=model_name,
            api_key=settings.OPENAI_API_KEY,
            temperature=0.2,
        )

    def analyze_chart_or_graph(self, user_query: str, image_path: str) -> str:
        """
        Encodes the image/chart, passes it to the Multimodal LLM along with the user prompt,
        and returns detailed text analysis.
        """
        base64_image = encode_image_to_base64(image_path)
        if not base64_image:
            return "Unable to process the image file. Please verify the image path."

        # System instructions specialized for PDF Charts/Graphs analysis
        system_prompt = (
            "You are an expert Data Analyst and Vision AI Specialist. "
            "Your job is to read and analyze PDF charts, graphs, diagrams, and figures. "
            "Provide clear, accurate, and structured insights based strictly on the visual data provided. "
            "If exact numbers/labels are visible in the chart, cite them directly."
        )

        # Multimodal Message Payload
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(
                content=[
                    {
                        "type": "text", 
                        "text": f"User Request: {user_query}\n\nPlease analyze this chart/graph and answer the query."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            )
        ]

        try:
            logger.info(f"VisionSubAgent analyzing image: {image_path}")
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"Error during Vision LLM invocation: {e}")
            return f"Failed to analyze the image due to an error: {str(e)}"


# ==========================================
# 🚀 LangGraph Node Integration Function
# ==========================================

def vision_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph Node for Vision Analysis.
    Reads `file_path` and last user message from AgentState, 
    runs visual analysis, and appends the response to `messages`.
    """
    messages = state.get("messages", [])
    file_path = state.get("file_path")
    
    # Extract last user message text
    user_query = "Summarize and analyze the key insights from this chart."
    if messages:
        last_msg = messages[-1]
        user_query = last_msg.get("content") if isinstance(last_msg, dict) else getattr(last_msg, "content", user_query)

    if not file_path:
        analysis_result = "No image or chart file path was provided for vision analysis."
    else:
        agent = VisionSubAgent()
        analysis_result = agent.analyze_chart_or_graph(user_query=user_query, image_path=file_path)

    # Append Assistant response back to State
    new_messages = list(messages)
    new_messages.append({"role": "assistant", "content": analysis_result})

    return {
        **state,
        "messages": new_messages,
        "next_node": "END"
    }
    """
vision_node.py

Vision Agent Node using ChatOpenAI (GPT-4o) with strict numerical reading rules.
"""

from typing import Any, Dict
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from backend.app.logger import logger
from agents.prompts import VISION_SYSTEM_PROMPT  # Importing updated prompt


llm_vision = ChatOpenAI(
    model="gpt-4o",
    temperature=0.0  # 🎯 Strict zero-temperature to avoid creative hallucination of numbers
)


def vision_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processes image/visual queries with strict numerical reading rules.
    """
    question = state.get("question", "")
    file_path = state.get("file_path") or state.get("image_path")

    if not file_path:
        logger.warning("Vision node invoked without an image/file path.")
        return {
            "messages": [
                HumanMessage(
                    content="Error: No image or visual file was provided for analysis."
                )
            ]
        }

    try:
        # Construct multimodal input message
        messages = [
            SystemMessage(content=VISION_SYSTEM_PROMPT),
            HumanMessage(
                content=[
                    {"type": "text", "text": question},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"file://{file_path}"},
                    },
                ]
            ),
        ]

        logger.info(f"Executing Vision Node for file: {file_path}")
        response = llm_vision.invoke(messages)

        return {
            "messages": [response],
            "context": response.content,
            "next_node": "end",
        }

    except Exception as e:
        logger.error(f"Vision Agent Node Error: {str(e)}")
        return {
            "messages": [
                HumanMessage(
                    content=f"Failed to process visual data accurately: {str(e)}"
                )
            ],
            "next_node": "end",
        }
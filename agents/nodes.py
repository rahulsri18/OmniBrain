from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from agents.output_parser import parse_retriever_output
from agents.prompts import SUPERVISOR_SYSTEM_PROMPT
from agents.retriever import retriever_tool
from agents.state import GraphState
from backend.app.sql_agent.agent import sql_agent_node

llm = ChatOpenAI(model="gpt-4o", temperature=0)


def router_node(state: GraphState) -> GraphState:
    """Supervisor node that routes the query using GPT-4o."""

    messages = [
        SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT),
        HumanMessage(content=state["question"]),
    ]

    response = llm.invoke(messages)
    route = response.content.strip().lower()

    valid_routes = {"retriever", "sql", "vision", "general"}
    if route not in valid_routes:
        route = "general"

    state["route"] = route

    # SQL Route
    if route == "sql":
        sql_query = sql_agent_node(state["question"])

        state.setdefault("metadata", {})
        state["metadata"]["sql_query"] = sql_query

        return state

    # Retriever / Vision / General Routes
    raw_documents = retriever_tool(state["question"])
    # 1. SQL Route Handling
    if route == "sql":
        sql_result = sql_agent_node(state["question"])
        if "metadata" not in state or state["metadata"] is None:
            state["metadata"] = {}

        state["metadata"]["sql_query"] = sql_result["sql_query"]
        state["context"] = [str(sql_result["data"])]
        return state

    # 2. Retriever (RAG) Route Handling
    elif route == "retriever":
        raw_documents = retriever_tool(state["question"])
        clean_context_list = parse_retriever_output(raw_documents)
        state["context"] = clean_context_list
        return state

    state["context"] = clean_context_list

    return state


def grader_node(state: GraphState) -> GraphState:
    """
    Day 11 - Document Grader Node

    Checks whether the retrieved context is useful.
    """

    context = state.get("context", [])

    state.setdefault("metadata", {})

    if context and len(context) > 0:
        state["metadata"]["grade"] = "accept"
    else:
        state["metadata"]["grade"] = "retry"

    return state


def routing_decider(state: GraphState) -> str:
    """
    Decide the next step after grading.
    """

    return state.get("metadata", {}).get("grade", "accept")
    # 3. Vision / General Fallback
    return state
    """
nodes.py - Example integration for Vision Node with M4 Fallback
"""

from backend.app.agents.vision_fallback import safe_vision_execution_wrapper, vision_error_handler_node
from backend.app.logger import logger

@safe_vision_execution_wrapper
def vision_node(state: dict) -> dict:
    """
    Vision processing node. If CLIP or Multi-modal LLM fails inside here, 
    the wrapper automatically catches it and returns the fallback state.
    """
    file_path = state.get("file_path")
    
    # Simulate processing (replace with actual CLIP / Vision LLM call)
    logger.info(f"Processing image at: {file_path}")
    
    # If vision model throws exception, wrapper catches it smoothly
    # e.g., raise RuntimeError("Vision API Timeout")

    state["context"] = f"Successfully extracted vision details from {file_path}"
    return state

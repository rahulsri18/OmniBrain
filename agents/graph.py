# agents/graph.py
from langgraph.graph import StateGraph, END
from agents.state import GraphState
from agents.nodes import router_node


def route_query(state: GraphState):
    return state.get("route", "general")


builder = StateGraph(GraphState)

builder.add_node("router", router_node)

builder.set_entry_point("router")

def route_query(state: GraphState) -> str:
    """
    Supervisor routing logic: State से 'route' की वैल्यू रीड करता है।
    अगर वैल्यू अननोन है या सेट नहीं है, तो सेफली 'end' पर फॉलबैक करता है।
    """
    route = state.get("route", "end")
    
    # 🚀 सेफ गार्ड: अगर रूट मैपिंग डिक्शनरी में नहीं है तो 'end' पर भेजो
    valid_routes = ["end"] # आगे चलकर यहाँ "rag", "sql", "general" जुड़ेंगे
    
    if route not in valid_routes:
        return "end"
        
    return route


# 1. StateGraph इनिशियलाइज़ करें
builder = StateGraph(GraphState)

# 2. नोड्स रजिस्टर करें
builder.add_node("router", router_node)

# 3. एंट्री पॉइंट सेट करें
builder.set_entry_point("router")

# 4. कंडीशनल एज कनेक्ट करें
builder.add_conditional_edges(
    "router",
    route_query,
    {
        "retriever": END,
        "sql": END,
        "vision": END,
        "general": END,
        "end": END,
        # भविष्य के नोड्स के लिए प्लेसहोलडर (Day 7 में इनेबल होंगे):
        # "rag": "rag_node",
        # "sql": "sql_node",
    },
)

# 5. ग्राफ कंपाइल करें
graph = builder.compile()
"""
graph.py

LangGraph Workflow Definition & Compiler.
"""

from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict):
    messages: List[Dict[str, Any]]
    session_id: str
    file_path: Optional[str]
    next_node: str

# Define nodes...
def router_node(state: AgentState):
    return state

# Build graph
workflow = StateGraph(AgentState)
workflow.add_node("router", router_node)
workflow.set_entry_point("router")
workflow.add_edge("router", END)

# 🚀 Compile LangGraph workflow
app_graph = workflow.compile()
from agents.vision_node import vision_node

# Add Node to LangGraph StateGraph
workflow.add_node("vision_node", vision_node)
"""
backend/app/agents/graph.py

LangGraph state machine with conditional routing and explicit error state fallback.
"""

from typing import Any, Dict, TypedDict
from langgraph.graph import END, StateGraph

# pyrefly: ignore [missing-import]
from agents.nodes.fallback import fallback_node


class GraphState(TypedDict):
    messages: list
    session_id: str
    question: str
    error: str
    next_step: str
    execution_status: str


def route_next_step(state: GraphState) -> str:
    """Conditional router that intercepts errors and redirects to the fallback node."""
    if state.get("error") or state.get("next_step") == "fallback_node":
        return "fallback"
    
    # Example routing logic for regular flow
    next_step = state.get("next_step", "end")
    if next_step == "end":
        return END
    return next_step


# Build Workflow
workflow = StateGraph(GraphState)

# Add Fallback Node
workflow.add_node("fallback", fallback_node)

# Example: Linking nodes (replace with your real nodes)
# workflow.add_node("grader", grader_node)
# workflow.add_conditional_edges("grader", route_next_step, {"fallback": "fallback", "end": END})

workflow.set_entry_point("fallback")  # Update to your entry point (e.g., supervisor)

app_graph = workflow.compile()
# agents/graph.py

def vision_router(state: AgentState) -> str:
    """Decides whether to proceed or trigger fallback based on image error flag."""
    if state.get("image_error"):
        return "fallback_node"  # Route to fallback/error handler
    return "grader_node"        # Proceed to next step

# Attach conditional edge after vision_node
workflow.add_conditional_edges(
    "vision_node",
    vision_router,
    {
        "fallback_node": "fallback_node",
        "grader_node": "grader_node"
    }
)
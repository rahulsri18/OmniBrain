from langgraph.graph import StateGraph, END

from agents.state import GraphState
from agents.nodes import (
    router_node,
    retrieve_node,
    generate_node,
)


# Create the graph
builder = StateGraph(GraphState)

# Add nodes
builder.add_node("router", router_node)
builder.add_node("retrieve", retrieve_node)
builder.add_node("generate", generate_node)

# Define flow
builder.set_entry_point("router")
builder.add_edge("router", "retrieve")
builder.add_edge("retrieve", "generate")
builder.add_edge("generate", END)

# Compile graph
graph = builder.compile()
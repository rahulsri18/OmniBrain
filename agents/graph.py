# agents/graph.py
from langgraph.graph import StateGraph, END
from agents.state import GraphState
from agents.nodes import router_node


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
        "end": END,
        # भविष्य के नोड्स के लिए प्लेसहोलडर (Day 7 में इनेबल होंगे):
        # "rag": "rag_node",
        # "sql": "sql_node",
    },
)

# 5. ग्राफ कंपाइल करें
graph = builder.compile()
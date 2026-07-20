# agents/nodes.py
from agents.state import GraphState
from agents.retriever import retriever_tool
from agents.output_parser import parse_retriever_output

def router_node(state: GraphState) -> GraphState:
    """
    Relevant context/documents को रिट्राइव और पार्स करके स्टेट में अपडेट करता है।
    """
    query = state["question"]

    # 1. रॉ डॉक्यूमेंट्स फेच करो
    raw_documents = retriever_tool(query)

    # 2. पार्सर से उसे क्लीन List[str] में बदलो
    clean_context_list = parse_retriever_output(raw_documents)

    # 3. स्टेट को सीधे लिस्ट असाइन करो (बिना एक्स्ट्रा ब्रैकेट के)
    state["context"] = clean_context_list

    return state
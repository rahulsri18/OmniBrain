from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from agents.state import GraphState
from agents.retriever import retriever_tool
from agents.output_parser import parse_retriever_output
from agents.prompts import SUPERVISOR_SYSTEM_PROMPT


llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0
)


def router_node(state: GraphState) -> GraphState:
    """
    Supervisor node that routes the query using GPT-4o.
    """

    messages = [
        SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT),
        HumanMessage(content=state["question"])
    ]

    response = llm.invoke(messages)

    route = response.content.strip().lower()

    valid_routes = {"retriever", "sql", "vision", "general"}

    if route not in valid_routes:
        route = "general"

    state["route"] = route

    raw_documents = retriever_tool(state["question"])

    clean_context_list = parse_retriever_output(raw_documents)

    state["context"] = clean_context_list

    return state
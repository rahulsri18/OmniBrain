from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from backend.app.sql_agent.agent import sql_agent_node
from backend.app.ingestion.query_transformer import QueryTransformer
from agents.langfuse_tracing import trace_node

from agents.state import GraphState
from agents.retriever import retriever_tool
from agents.output_parser import parse_retriever_output
from agents.prompts import SUPERVISOR_SYSTEM_PROMPT


llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0
)

def rewrite_call(system_prompt: str, user_prompt: str) -> str:
    """
    Adapter so QueryTransformer can use ChatOpenAI.
    """
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]

    response = llm.invoke(messages)

    return response.content
transformer = QueryTransformer(
    call_fn=rewrite_call
)
@trace_node("router")
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

    # SQL Route
    if route == "sql":
        sql_query = sql_agent_node(state["question"])

        state.setdefault("metadata", {})
        state["metadata"]["sql_query"] = sql_query

        return state

    # Retriever / Vision / General Routes
    raw_documents = retriever_tool(state["question"])

    clean_context_list = parse_retriever_output(raw_documents)

    state["context"] = clean_context_list

    return state

@trace_node("grader")
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
@trace_node("query_rewriter")
def query_rewriter_node(state: GraphState) -> GraphState:
    """
    Day 12 - Query Rewriter Node

    Rewrites the user's query when retrieval quality is poor.
    """

    result = transformer.transform(
        original_query=state["question"]
    )

    # Update rewritten query
    state["question"] = result.rewritten_query

    # Increment retry count
    state["loop_count"] += 1

    state.setdefault("metadata", {})
    state["metadata"]["rewritten"] = not result.used_fallback

    return state

def routing_decider(state: GraphState) -> str:
    """
    Decide the next step after grading.
    """

    grade = state.get("metadata", {}).get("grade", "accept")

    if grade == "retry":
        if state["loop_count"] >= state["max_loops"]:
            return "accept"
        return "retry"

    return "accept"
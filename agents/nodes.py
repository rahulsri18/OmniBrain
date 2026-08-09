from langchain_core.messages import AIMessage
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
# ==========================================================
# Day 16 - Parallel Execution Nodes
# ==========================================================

@trace_node("sql")
def sql_node(state: GraphState) -> GraphState:
    """
    Executes SQL retrieval independently.
    """
    result = sql_agent_node(state["question"])

    state["sql_result"] = result

    return state


@trace_node("retriever")
def retriever_node(state: GraphState) -> GraphState:
    """
    Executes vector retrieval independently.
    """

    raw_documents = retriever_tool(state["question"])

    clean_context = parse_retriever_output(raw_documents)

    state["retriever_result"] = clean_context

    return state


@trace_node("merge")
def merge_node(state: GraphState) -> GraphState:
    """
    Merge outputs from SQL and Retriever branches.
    """

    merged_context = []

    if state.get("retriever_result"):
        merged_context.extend(state["retriever_result"])

    if state.get("sql_result"):
        merged_context.append(str(state["sql_result"]))

    state["merged_context"] = merged_context
    state["context"] = merged_context

    return state
async def fallback_node(state: GraphState) -> GraphState:
    """
    Handles graceful recovery when upstream nodes fail
    or route to an error state.
    """

    error_detail = state.get(
        "error",
        "An unexpected runtime error occurred."
    )

    fallback_message = (
        "I encountered a temporary glitch while processing your request. "
        "Please try rephrasing your prompt or uploading the document again."
    )

    state.setdefault("metadata", {})

    state["error"] = error_detail
    state["metadata"]["execution_status"] = "failed_gracefully"

    state.setdefault("chat_history", [])
    state["chat_history"].append({
        "role": "assistant",
        "content": fallback_message,
    })

    state["response"] = fallback_message

    return state
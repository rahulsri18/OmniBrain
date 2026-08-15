from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from backend.app.sql_agent.agent import sql_agent_node
from backend.app.ingestion.query_transformer import QueryTransformer
from agents.langfuse_tracing import trace_node
from backend.app.config import settings


from agents.state import GraphState
from agents.retriever import retriever_tool
from agents.output_parser import parse_retriever_output
from agents.prompts import SUPERVISOR_SYSTEM_PROMPT


llm = ChatOpenAI(
    model=settings.GEMINI_MODEL,
    api_key=settings.GEMINI_API_KEY,
    base_url=settings.GEMINI_BASE_URL,
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
    Supervisor node that only decides which route should execute.

    Routes:
    - sql
    - retriever
    - vision
    - hybrid
    - general

    IMPORTANT:
    This node does NOT execute SQL or retrieval.
    The graph sends the state to the appropriate execution node.
    """

    question = state["question"].strip()
    question_lower = question.lower()
    file_path = state.get("file_path")

    # ==========================================================
    # Keyword groups
    # ==========================================================

    vision_keywords = [
        "image",
        "picture",
        "photo",
        "uploaded image",
        "uploaded picture",
        "uploaded photo",
        "visual",
        "vision",
        "describe the image",
        "describe this image",
    ]

    sql_keywords = [
        "database",
        "sql",
        "sales",
        "customers",
        "customer",
        "employees",
        "employee",
        "salary",
        "salaries",
        "total",
        "count",
        "records",
        "rows",
        "table",
        "region",
        "active customers",
    ]

    retriever_keywords = [
        "pdf",
        "document",
        "uploaded document",
        "uploaded pdf",
        "page ",
        "contract",
        "report",
        "summarize my uploaded",
        "summarize the uploaded",
        "according to the document",
        "in the document",
    ]

    # ==========================================================
    # Detect query types
    # ==========================================================

    is_vision = any(
        keyword in question_lower
        for keyword in vision_keywords
    )

    is_sql = any(
        keyword in question_lower
        for keyword in sql_keywords
    )

    is_retriever = any(
        keyword in question_lower
        for keyword in retriever_keywords
    )

    # ==========================================================
    # Deterministic routing
    # ==========================================================

    # Vision takes priority
    if is_vision:
        route = "vision"

    # Query needs both SQL + document retrieval
    elif is_sql and is_retriever:
        route = "hybrid"

    # SQL only
    elif is_sql:
        route = "sql"

    # Document / PDF only
    elif is_retriever:
        route = "retriever"

    # Greetings / clearly general
    elif any(
        question_lower.startswith(greeting)
        for greeting in [
            "hello",
            "hi",
            "hey",
            "good morning",
            "good afternoon",
            "good evening",
        ]
    ):
        route = "general"
        
    # If a document is attached/provided and the query is not
    # clearly SQL or vision-related, use document retrieval.
    elif file_path:
        route = "retriever"

    # ==========================================================
    # LLM fallback for ambiguous questions
    # ==========================================================
    else:
        messages = [
            SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT),
            HumanMessage(content=question),
        ]

        response = llm.invoke(messages)

        route = response.content.strip().lower()

        valid_routes = {
            "retriever",
            "sql",
            "vision",
            "hybrid",
            "general",
        }

        if route not in valid_routes:
            route = "general"

    # ==========================================================
    # Store route only
    # ==========================================================

    state["route"] = route

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
    merged_context = []

    if state.get("retriever_result"):
        merged_context.extend(state["retriever_result"])

    if state.get("sql_result"):
        merged_context.append(str(state["sql_result"]))

    state["merged_context"] = merged_context
    state["context"] = merged_context   # now a clean overwrite, not an append
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
    state["answer"] = fallback_message 

    return state
from langchain_core.messages import SystemMessage, HumanMessage

GENERATION_SYSTEM_PROMPT = """You are OmniBrain, an assistant that answers questions using only the
provided context. Cite the source of each claim where possible. If the context doesn't contain
enough information to answer, say so clearly instead of guessing."""

@trace_node("generate")
async def generate_node(state: GraphState) -> GraphState:
    """
    Synthesizes a final natural-language answer from the merged/graded context.
    Uses .astream() so LangGraph emits on_chat_model_stream events that
    main.py's chat_stream() listens for.
    """
    context_text = "\n\n".join(state.get("context", [])) or "No relevant context was found."

    messages = [
        SystemMessage(content=GENERATION_SYSTEM_PROMPT),
        HumanMessage(content=f"Context:\n{context_text}\n\nQuestion: {state['question']}"),
    ]

    full_response = ""
    async for chunk in llm.astream(messages):
        if chunk.content:
            full_response += chunk.content

    state["response"] = full_response
    state["answer"] = full_response   # also populate this so output_guardrail's check is meaningful
    return state
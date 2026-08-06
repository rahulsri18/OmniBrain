from agents.state import GraphState


def output_validation_rail_node(state: GraphState) -> GraphState:
    """
    Day 18 - Graceful Output Recovery

    Ensures every failure path returns a clear,
    user-friendly response instead of exposing
    raw errors or empty outputs.
    """

    answer = state.get("answer", "").strip()
    error = state.get("error")

    state.setdefault("metadata", {})

    if error:

        error_text = str(error).lower()

        if "blocked" in error_text:
            message = (
                "Your request could not be processed because it violates "
                "the system safety policy."
            )

        elif "vision" in error_text or "image" in error_text:
            message = (
                "The uploaded image or chart could not be processed. "
                "Please upload a clearer file and try again."
            )

        elif "sql" in error_text:
            message = (
                "The requested database information could not be retrieved."
            )

        elif "retriever" in error_text:
            message = (
                "Relevant information could not be retrieved for this query."
            )

        else:
            message = (
                "An unexpected error occurred while processing your request. "
                "Please try again."
            )

        state["answer"] = message
        state["metadata"]["output_blocked"] = True

    elif not answer:

        state["answer"] = (
            "No response could be generated for this request."
        )
        state["metadata"]["output_blocked"] = True

    else:
        state["metadata"]["output_blocked"] = False

    return state
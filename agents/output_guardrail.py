from agents.state import GraphState


SAFE_FALLBACK_MESSAGE = (
    "I'm unable to provide a reliable response for this request."
)


def output_validation_rail_node(state: GraphState) -> GraphState:
    """
    Day 18 - Graceful Output Recovery

    Ensures every failure path returns a clear,
    user-friendly response instead of exposing
    raw errors or empty outputs.
    """

    answer = state.get("answer", "")

    if answer is None:
        answer = ""

    answer = str(answer).strip()

    error = state.get("error")

    state.setdefault("metadata", {})

    # Check whether the input was already blocked.
    blocked = bool(
        state.get("blocked", False)
        or state["metadata"].get("blocked", False)
    )

    # Any blocked input, error, or empty answer gets a safe fallback.
    if blocked or error or not answer:
        state["answer"] = SAFE_FALLBACK_MESSAGE
        state["metadata"]["output_blocked"] = True
        return state

    # Valid answer
    state["metadata"]["output_blocked"] = False

    return state
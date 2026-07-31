from agents.state import GraphState


def output_validation_rail_node(state: GraphState) -> GraphState:
    """
    Day 14 - Output Validation Rail

    Validates the final response before returning it.
    """

    answer = state.get("answer", "")

    state.setdefault("metadata", {})

    blocked = (
        state.get("metadata", {}).get("blocked", False)
        or state.get("error") is not None
    )

    if blocked or not answer.strip():
        state["answer"] = (
            "I'm unable to provide a reliable response for this request."
        )
        state["metadata"]["output_blocked"] = True
    else:
        state["metadata"]["output_blocked"] = False

    return state
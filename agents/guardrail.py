from agents.state import GraphState


BLOCKED_KEYWORDS = {
    "hack",
    "hacking",
    "malware",
    "virus",
    "exploit",
    "phishing",
    "abuse",
    "terrorism",
    "politics",
}


def input_safety_rail_node(state: GraphState) -> GraphState:
    """
    Day 13 - Input Safety Rail Node

    Checks the user's prompt before entering the LangGraph workflow.
    Blocks prompts containing restricted keywords.
    """

    question = state.get("question", "").lower()

    state.setdefault("metadata", {})

    blocked = [
        keyword
        for keyword in BLOCKED_KEYWORDS
        if keyword in question
    ]

    if blocked:
        state["error"] = (
            f"Blocked by input safety rail. "
            f"Restricted keyword(s): {', '.join(blocked)}"
        )
        state["metadata"]["blocked"] = True
    else:
        state["metadata"]["blocked"] = False

    return state
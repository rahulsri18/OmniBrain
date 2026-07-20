from typing import List


def parse_retriever_output(documents: List[str]) -> str:
    """
    Convert retrieved documents into a prompt-friendly string.
    """

    if not documents:
        return "No relevant context found."

    return "\n\n".join(documents)
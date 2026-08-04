"""
agents/nodes/transformer_node.py

Invokes M2's QueryTransformer and increments the graph's loop_count.
"""

from typing import Any, Dict
# pyrefly: ignore [missing-import
from agents.ingestion.query_transformer import QueryTransformer


async def transform_query_node(state: Dict[str, Any], transformer_instance: QueryTransformer) -> Dict[str, Any]:
    """
    Node that rewrites the user query and updates loop_count.
    """
    original_query = state.get("question", "")
    current_loop = state.get("loop_count", 0)

    # Call M2's QueryTransformer
    transform_result = transformer_instance.transform(original_query)
    
    return {
        **state,
        "rewritten_query": transform_result.rewritten_query,
        "loop_count": current_loop + 1,  # Increment loop counter
    }
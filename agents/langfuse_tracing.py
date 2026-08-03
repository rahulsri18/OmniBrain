"""
Langfuse tracing utilities for LangGraph nodes.
"""

import functools
import logging

logger = logging.getLogger(__name__)


def trace_node(node_name: str):
    """
    Decorator for tracing LangGraph nodes.

    Currently logs node execution.
    Can later be connected to Langfuse SDK.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(state, *args, **kwargs):
            logger.info(f"[Langfuse] Starting node: {node_name}")

            result = func(state, *args, **kwargs)

            logger.info(f"[Langfuse] Finished node: {node_name}")

            return result

        return wrapper

    return decorator
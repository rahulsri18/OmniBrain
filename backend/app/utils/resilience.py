"""
backend/app/agents/utils/resilience.py

Provides retry decorators and execution wrappers to safely handle 
transient errors inside graph nodes.
"""

import asyncio
import logging
from typing import Any, Callable, Dict

logger = logging.getLogger("OmniBrain.Resilience")


def safe_node_execute(
    fallback_node_name: str = "fallback_node",
    max_retries: int = 2,
    retry_delay: float = 1.0,
):
    """
    Decorator for graph nodes that retries on transient errors and catches 
    fatal exceptions, setting an error state without breaking the graph pipeline.
    """
    def decorator(func: Callable):
        async def wrapper(state: Dict[str, Any], *args, **kwargs) -> Dict[str, Any]:
            last_exception = None

            for attempt in range(1, max_retries + 2):
                try:
                    return await func(state, *args, **kwargs)
                except Exception as exc:
                    last_exception = exc
                    logger.warning(
                        f"Attempt {attempt}/{max_retries + 1} failed in node '{func.__name__}': {str(exc)}"
                    )
                    if attempt <= max_retries:
                        await asyncio.sleep(retry_delay * (2 ** (attempt - 1)))

            # Log fatal node error and route to fallback state
            logger.error(
                f"Fatal node error in '{func.__name__}' after {max_retries} retries: {str(last_exception)}"
            )
            return {
                **state,
                "error": f"Error in {func.__name__}: {str(last_exception)}",
                "next_step": fallback_node_name,
            }

        return wrapper
    return decorator
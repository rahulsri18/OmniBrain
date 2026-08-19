import json
from typing import Any, AsyncGenerator
from app.logger import logger


async def stream_formatter(
    stream: AsyncGenerator[Any, None]
) -> AsyncGenerator[str, None]:
    """
    Format streamed response before sending to frontend via SSE.
    Handles Assistant content, Agent Steps/Reasoning, and Error tokens safely.
    """
    try:
        async for event in stream:
            if event is None:
                continue

            # 1. Plain String Tokens
            if isinstance(event, str):
                yield f"data: {json.dumps({'type': 'content', 'content': event})}\n\n"

            # 2. Dictionary Events
            elif isinstance(event, dict):
                event_type = event.get("type")

                # Filter out raw internal telemetry if not required on UI
                internal_events = {"debug", "internal", "system"}
                if event_type in internal_events:
                    continue

                # 🚨 Handle Explicit Error Tokens from Stream
                if event_type == "error":
                    error_msg = event.get("content") or event.get("message") or "An streaming error occurred."
                    logger.error(f"SSE Stream Formatter caught Error Event: {error_msg}")


                    error_payload = json.dumps({
                        "type": "error",
                        "status": event.get("status", "error"),
                        "reason": event.get("reason"),
                        "message": error_msg
                    })


                    yield f"data: {error_payload}\n\n"
                    continue

                # 💬 Stream Content / Assistant Tokens
                content = event.get("content")
                if content:
                    yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"

                # 🧠 Stream Reasoning / Thought Steps
                elif event_type == "reasoning":
                    yield f"data: {json.dumps(event)}\n\n"

            # 3. Unknown Data Types Fallback
            else:
                yield f"data: {json.dumps({'type': 'content', 'content': str(event)})}\n\n"

    except Exception as exc:
        logger.error(f"Unhandled Exception inside stream_formatter generator: {str(exc)}")
        err_payload = json.dumps({
            "type": "error",
            "message": f"Stream processing failed unexpectedly: {str(exc)}"
        })
        yield f"data: {err_payload}\n\n"

    finally:
        # Notify SSE completion standard
        yield "data: [DONE]\n\n"
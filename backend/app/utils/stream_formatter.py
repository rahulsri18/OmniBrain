from typing import AsyncGenerator, Any
import json


# Format streamed response before sending to frontend
async def stream_formatter(stream: AsyncGenerator[Any, None]) -> AsyncGenerator[str, None]:

    # Read every event from the stream
    async for event in stream:

        # Skip empty events
        if event is None:
            continue

        # Stream plain text directly
        if isinstance(event, str):
            yield f"data: {event}\n\n"

        # Stream only user-facing content
        elif isinstance(event, dict):

            # Ignore internal agent events
            internal_events = {"tool","debug", "metadata", "internal", "system"}
            
            if event.get("type") in internal_events:
                continue

            # Stream assistant response
            content = event.get("content")

            if content:
                yield f"data: {content}\n\n"

        # Convert unknown objects into JSON
        else:
            yield f"data: {json.dumps(str(event))}\n\n"

    # Notify frontend that streaming is complete
    yield "data: [DONE]\n\n"
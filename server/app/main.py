
from pydantic_ai import (
    AgentRunResultEvent,
    FinalResultEvent,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    PartStartEvent,
    TextPart,
    TextPartDelta,
    ThinkingPart,
    ThinkingPartDelta,
)


from .agent import AgentDeps, orchestrator
from .schemas import ChatRequest
from .sse import sse_event
from fastapi.middleware.cors import CORSMiddleware
import traceback
from fastapi import FastAPI
import uuid
from fastapi.responses import StreamingResponse


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


async def stream_agent_response(message: str, location: str):
    run_id = str(uuid.uuid4())
    assistant_message_id = str(uuid.uuid4())

    yield sse_event(
        "RUN_STARTED",
        {
            "run_id": run_id,
            "message_id": assistant_message_id,
        },
    )

    yield sse_event(
        "TRACE_START",
        {
            "title": "Reasoning",
            "collapsed": True,
        },
    )

    final_text_started = False

    try:
        deps = AgentDeps(user_location=location)

        async for event in orchestrator.run_stream_events(message, deps=deps):
            if isinstance(event, PartStartEvent):
                if isinstance(event.part, ThinkingPart):
                    yield sse_event(
                        "THINKING_START",
                        {
                            "message_id": assistant_message_id,
                        },
                    )
                elif isinstance(event.part, TextPart):
                    if not final_text_started:
                        final_text_started = True
                        yield sse_event(
                            "TEXT_MESSAGE_START",
                            {
                                "message_id": assistant_message_id,
                                "role": "assistant",
                            },
                        )

            elif isinstance(event, PartDeltaEvent):
                if isinstance(event.delta, ThinkingPartDelta):
                    if event.delta.content_delta:
                        yield sse_event(
                            "THINKING_DELTA",
                            {
                                "delta": event.delta.content_delta,
                            },
                        )

                elif isinstance(event.delta, TextPartDelta):
                    if not final_text_started:
                        final_text_started = True
                        yield sse_event(
                            "TEXT_MESSAGE_START",
                            {
                                "message_id": assistant_message_id,
                                "role": "assistant",
                            },
                        )

                    if event.delta.content_delta:
                        yield sse_event(
                            "TEXT_MESSAGE_CHUNK",
                            {
                                "message_id": assistant_message_id,
                                "delta": event.delta.content_delta,
                            },
                        )

            elif isinstance(event, FunctionToolCallEvent):
                tool_name = getattr(event, "tool_name", None) or getattr(event.part, "tool_name", "unknown_tool")

                yield sse_event(
                    "TOOL_CALL",
                    {
                        "tool_name": tool_name,
                        "node_id": str(uuid.uuid4()),
                    },
                )

            elif isinstance(event, FunctionToolResultEvent):
                tool_name = getattr(event, "tool_name", "unknown_tool")

                yield sse_event(
                    "TOOL_DONE",
                    {
                        "tool_name": tool_name,
                    },
                )

            elif isinstance(event, FinalResultEvent):
                yield sse_event(
                    "FINAL_RESULT_MARK",
                    {
                        "message_id": assistant_message_id,
                    },
                )

            elif isinstance(event, AgentRunResultEvent):
                yield sse_event(
                    "TEXT_MESSAGE_END",
                    {
                        "message_id": assistant_message_id,
                    },
                )

        yield sse_event(
            "TRACE_END",
            {
                "title": "Reasoning",
            },
        )

        yield sse_event("RUN_FINISHED", {"run_id": run_id})

    except Exception as e:
        traceback.print_exc()
        yield sse_event(
            "RUN_ERROR",
            {
                "error": str(e),
            },
        )


@app.post("/agent")
async def run_agent(req: ChatRequest):
    return StreamingResponse(
        stream_agent_response(req.message, req.location),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/health")
async def health():
    return {"status": "ok"}
import traceback
import uuid

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .memory import load_thread_context, save_message
from .schemas import ChatRequest
from .sse import sse_event
from .state import WorkflowState
from .workflow import (
    memory_node,
    planner_node,
    parallel_workers_node,
    synthesizer_stream,
)


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


async def stream_agent_response(message: str, location: str, thread_id: str | None):
    run_id = str(uuid.uuid4())
    assistant_message_id = str(uuid.uuid4())

    yield sse_event("RUN_STARTED", {"run_id": run_id, "message_id": assistant_message_id})
    yield sse_event("TRACE_START", {"title": "Reasoning timeline", "collapsed": True})

    state = WorkflowState(
        thread_id=thread_id,
        user_message=message,
        user_location=location,
        thread_context=load_thread_context(thread_id),
    )

    try:
        memory_event = await memory_node(state)
        yield sse_event(memory_event["event_type"], memory_event["payload"])

        yield sse_event("PLANNER_STEP", {"delta": "Understand the request\n"})
        planner_event = await planner_node(state)
        yield sse_event(planner_event["event_type"], planner_event["payload"])

        yield sse_event("PLANNER_STEP", {"delta": "Run required worker tasks\n"})

        results = await parallel_workers_node(state)

        for idx, (tool_name, _output) in enumerate(results, start=1):
            yield sse_event(
                "TOOL_CALL",
                {
                    "tool_name": tool_name,
                    "node_id": f"{tool_name}-{idx}",
                },
            )
            yield sse_event("TOOL_DONE", {"tool_name": tool_name})

        yield sse_event("SYNTHESIS_START", {"delta": "Drafting final answer\n"})

        yield sse_event(
            "TEXT_MESSAGE_START",
            {
                "message_id": assistant_message_id,
                "role": "assistant",
            },
        )

        final_text = ""
        async for chunk in synthesizer_stream(state):
            final_text += chunk
            yield sse_event(
                "TEXT_MESSAGE_CHUNK",
                {
                    "message_id": assistant_message_id,
                    "delta": chunk,
                },
            )

        yield sse_event("TEXT_MESSAGE_END", {"message_id": assistant_message_id})

        save_message(thread_id, "user", message)
        save_message(thread_id, "assistant", final_text)

        yield sse_event("TRACE_END", {"title": "Reasoning timeline"})
        yield sse_event("RUN_FINISHED", {"run_id": run_id})

    except Exception as e:
        traceback.print_exc()
        yield sse_event("RUN_ERROR", {"error": str(e)})


@app.post("/agent")
async def run_agent(req: ChatRequest):
    return StreamingResponse(
        stream_agent_response(req.message, req.location, req.thread_id),
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
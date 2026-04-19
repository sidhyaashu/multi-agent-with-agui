import asyncio
import re

from .agent import (
    AgentDeps,
    planner_agent,
    synthesizer_agent,
    weather_agent,
    calculator_agent,
    research_agent,
)
from .state import WorkflowState, TaskItem


def detect_tasks(user_message: str) -> list[TaskItem]:
    text = user_message.lower()
    tasks: list[TaskItem] = []

    weather_keywords = ["weather", "temperature", "rain", "umbrella", "forecast"]
    news_keywords = ["latest", "news", "recent", "current", "today"]
    math_ops = ["+", "-", "*", "/", "%"]

    if any(k in text for k in weather_keywords):
        cities = []
        if "tokyo" in text:
            cities.append("Tokyo")
        if "kolkata" in text:
            cities.append("Kolkata")
        if "delhi" in text:
            cities.append("Delhi")
        if not cities:
            cities.append("Kolkata")

        for city in cities:
            tasks.append(TaskItem(kind="weather", payload={"city": city}))

    if any(op in text for op in math_ops) and any(ch.isdigit() for ch in text):
        tasks.append(TaskItem(kind="calculation", payload={"expression": user_message}))

    if any(k in text for k in news_keywords):
        tasks.append(TaskItem(kind="research", payload={"query": user_message}))

    if not tasks:
        tasks.append(TaskItem(kind="research", payload={"query": user_message}))

    return tasks


def summarize_task_types(tasks: list[TaskItem]) -> str:
    parts = []
    for task in tasks:
        if task.kind == "weather":
            parts.append(f"weather({task.payload['city']})")
        elif task.kind == "calculation":
            parts.append("calculation")
        elif task.kind == "research":
            parts.append("research")
    return ", ".join(parts)


async def memory_node(state: WorkflowState):
    return {
        "event_type": "MEMORY_LOOKUP",
        "payload": {
            "summary": "Loaded recent thread context",
        },
    }


async def planner_node(state: WorkflowState):
    deps = AgentDeps(
        user_location=state.user_location,
        thread_context=state.thread_context,
    )

    prompt = (
        f"Thread context:\n{state.thread_context}\n\n"
        f"User request:\n{state.user_message}\n\n"
        "Return a short routing summary."
    )

    result = await planner_agent.run(prompt, deps=deps)
    state.planner_summary = result.output
    state.tasks = detect_tasks(state.user_message)

    return {
        "event_type": "ROUTE_DECISION",
        "payload": {
            "delta": state.planner_summary + f"\nTasks: {summarize_task_types(state.tasks)}",
        },
    }


async def worker_node(task: TaskItem, state: WorkflowState):
    deps = AgentDeps(
        user_location=state.user_location,
        thread_context=state.thread_context,
    )

    if task.kind == "weather":
        tool_name = "get_weather"
        state.tool_calls.append(tool_name)

        result = await weather_agent.run(
            f"What is the weather in {task.payload['city']}?",
            deps=deps,
        )
        return tool_name, result.output

    if task.kind == "calculation":
        tool_name = "calculate_expression"
        state.tool_calls.append(tool_name)

        result = await calculator_agent.run(
            f"Calculate this carefully: {task.payload['expression']}",
            deps=deps,
        )
        return tool_name, result.output

    tool_name = "web_search"
    state.tool_calls.append(tool_name)

    result = await research_agent.run(
        f"Research and summarize: {task.payload['query']}",
        deps=deps,
    )
    return tool_name, result.output


async def parallel_workers_node(state: WorkflowState):
    coroutines = [worker_node(task, state) for task in state.tasks]
    results = await asyncio.gather(*coroutines)

    for idx, (tool_name, output) in enumerate(results, start=1):
        key = f"{tool_name}_{idx}"
        state.tool_outputs[key] = output

    return results


async def synthesizer_stream(state: WorkflowState):
    deps = AgentDeps(
        user_location=state.user_location,
        thread_context=state.thread_context,
    )

    prompt = (
        f"Thread context:\n{state.thread_context}\n\n"
        f"User request:\n{state.user_message}\n\n"
        f"Planner summary:\n{state.planner_summary}\n\n"
        f"Worker outputs:\n{state.tool_outputs}\n\n"
        "Write the final assistant response."
    )

    async with synthesizer_agent.run_stream(prompt, deps=deps) as result:
        async for chunk in result.stream_text(delta=True):
            if chunk:
                yield chunk
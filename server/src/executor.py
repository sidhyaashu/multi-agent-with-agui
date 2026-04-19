import asyncio
from dataclasses import dataclass

from .agent import (
    AgentDeps,
    planner_agent,
    synthesizer_agent,
    weather_agent,
    calculator_agent,
    research_agent,
)


@dataclass
class ExecutionResult:
    planner_summary: str
    timeline_steps: list[str]
    tool_calls: list[str]
    tool_outputs: dict[str, str]


def detect_tasks(user_message: str) -> list[dict]:
    text = user_message.lower()
    tasks = []

    has_weather = "weather" in text or "temperature" in text or "rain" in text
    has_news = "latest" in text or "news" in text or "recent" in text or "current" in text
    has_math = any(ch.isdigit() for ch in text) and any(op in text for op in ["+", "-", "*", "/", "%"])

    if has_weather:
        # very simple extraction for now
        if "tokyo" in text:
            tasks.append({"type": "weather", "city": "Tokyo"})
        if "kolkata" in text:
            tasks.append({"type": "weather", "city": "Kolkata"})
        if not any(task["type"] == "weather" for task in tasks):
            tasks.append({"type": "weather", "city": "Kolkata"})

    if has_news:
        tasks.append({"type": "research", "query": user_message})

    if has_math:
        tasks.append({"type": "calculation", "expression": user_message})

    if not tasks:
        tasks.append({"type": "research", "query": user_message})

    return tasks


async def run_tasks_in_parallel(tasks: list[dict], deps: AgentDeps):
    coroutines = []

    for task in tasks:
        if task["type"] == "weather":
            coroutines.append(
                weather_agent.run(
                    f"What is the weather in {task['city']}?",
                    deps=deps,
                )
            )
        elif task["type"] == "calculation":
            coroutines.append(
                calculator_agent.run(
                    f"Calculate this carefully: {task['expression']}",
                    deps=deps,
                )
            )
        elif task["type"] == "research":
            coroutines.append(
                research_agent.run(
                    f"Research and summarize: {task['query']}",
                    deps=deps,
                )
            )

    return await asyncio.gather(*coroutines, return_exceptions=False)


async def execute_request(user_message: str, deps: AgentDeps) -> ExecutionResult:
    planner_result = await planner_agent.run(
        f"Thread context:\n{deps.thread_context}\n\nUser request:\n{user_message}",
        deps=deps,
    )

    tasks = detect_tasks(user_message)

    timeline_steps = [
        "Understand the request",
        "Choose the required task(s)",
    ]

    tool_calls = []
    for task in tasks:
        if task["type"] == "weather":
            tool_calls.append("get_weather")
        elif task["type"] == "calculation":
            tool_calls.append("calculate_expression")
        elif task["type"] == "research":
            tool_calls.append("web_search")

    results = await run_tasks_in_parallel(tasks, deps=deps)

    tool_outputs: dict[str, str] = {}
    for task, result in zip(tasks, results):
        key = task["type"]
        tool_outputs[f"{key}_{len(tool_outputs)+1}"] = result.output

    timeline_steps.append("Gather tool results")
    timeline_steps.append("Draft final answer")

    return ExecutionResult(
        planner_summary=planner_result.output,
        timeline_steps=timeline_steps,
        tool_calls=tool_calls,
        tool_outputs=tool_outputs,
    )
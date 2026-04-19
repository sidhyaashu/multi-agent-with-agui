import os
from dataclasses import dataclass

from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext
from pydantic_ai.capabilities import Thinking
from pydantic_ai.models.openrouter import OpenRouterModel
from pydantic_ai.providers.openrouter import OpenRouterProvider
from .tools import calculate_expression, get_weather, web_search




load_dotenv()

@dataclass
class AgentDeps:
    user_location: str = "Kolkata"

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv("MODEL_NAME")


if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY not found")
if not MODEL:
    raise ValueError("MODEL not found")

model = OpenRouterModel(
    model_name=MODEL,
    provider=OpenRouterProvider(api_key=OPENROUTER_API_KEY),
)

weather_specialist = Agent(
    model=model,
    deps_type=AgentDeps,
    system_prompt=(
        "You are a weather specialist. "
        "Use the get_weather_data tool when needed. "
        "Answer clearly and briefly."
    ),
)

calculator_specialist = Agent(
    model=model,
    deps_type=AgentDeps,
    system_prompt=(
        "You are a precise calculation specialist. "
        "Always use the run_calculation tool for arithmetic or math."
    ),
)

research_specialist = Agent(
    model=model,
    deps_type=AgentDeps,
    system_prompt=(
        "You are a web research specialist. "
        "Use the run_web_search tool for recent or external facts. "
        "Summarize cleanly with source URLs if available."
    ),
)

@weather_specialist.tool
async def get_weather_data(ctx: RunContext[AgentDeps], city: str) -> dict:
    return await get_weather(city)

@calculator_specialist.tool
async def run_calculation(ctx: RunContext[AgentDeps], expression: str) -> dict:
    return await calculate_expression(expression)

@research_specialist.tool
async def run_web_search(ctx: RunContext[AgentDeps], query: str) -> dict:
    return await web_search(query)

orchestrator = Agent(
    model=model,
    deps_type=AgentDeps,
    system_prompt=(
        "You are a ReAct-style orchestrator.\n"
        "Decide which tool or specialist is needed based on the user request.\n"
        "Rules:\n"
        "- For weather requests, use delegate_weather.\n"
        "- For calculations, formulas, arithmetic, percentages, interest, algebra, use delegate_calculation.\n"
        "- For latest, news, current, recent, external knowledge, use delegate_research.\n"
        "- You may call more than one tool if needed.\n"
        "- Keep the final answer clean and user-facing.\n"
        "- Do not expose raw tool JSON unless the user asks.\n"
    ),
    capabilities=[
        Thinking(effort="medium"),
    ],
)


@orchestrator.tool
async def delegate_weather(ctx: RunContext[AgentDeps], city: str) -> str:
    result = await weather_specialist.run(f"What's the weather in {city}?", deps=ctx.deps)
    return result.output

@orchestrator.tool
async def delegate_calculation(ctx: RunContext[AgentDeps], expression: str) -> str:
    result = await calculator_specialist.run(
        f"Calculate this carefully: {expression}",
        deps=ctx.deps,
    )
    return result.output

@orchestrator.tool
async def delegate_research(ctx: RunContext[AgentDeps], query: str) -> str:
    result = await research_specialist.run(
        f"Research this and summarize: {query}",
        deps=ctx.deps,
    )
    return result.output


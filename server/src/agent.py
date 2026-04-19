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
    thread_context: str = ""


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

PLANNER_MODEL_NAME = os.getenv(
    "PLANNER_MODEL_NAME",
    "qwen/qwen3-next-80b-a3b-thinking",
)
WORKER_MODEL_NAME = os.getenv(
    "WORKER_MODEL_NAME",
    "qwen/qwen3-next-80b-a3b-instruct:free",
)

if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY not found")

planner_model = OpenRouterModel(
    model_name=PLANNER_MODEL_NAME,
    provider=OpenRouterProvider(api_key=OPENROUTER_API_KEY),
)

worker_model = OpenRouterModel(
    model_name=WORKER_MODEL_NAME,
    provider=OpenRouterProvider(api_key=OPENROUTER_API_KEY),
)


planner_agent = Agent(
    model=planner_model,
    deps_type=AgentDeps,
    output_type=str,
    system_prompt=(
        "You are a planning agent.\n"
        "Use the thread context and user request.\n"
        "Return a short routing summary.\n"
        "Mention which task types are needed: weather, calculation, research.\n"
        "Keep it short and structured."
    ),
    capabilities=[Thinking(effort="medium")],
)

synthesizer_agent = Agent(
    model=worker_model,
    deps_type=AgentDeps,
    output_type=str,
    system_prompt=(
        "You are the final assistant.\n"
        "Use the provided thread context and worker outputs.\n"
        "Write a clean, helpful final answer.\n"
        "Do not expose raw JSON."
    ),
)

weather_agent = Agent(
    model=worker_model,
    deps_type=AgentDeps,
    output_type=str,
    system_prompt="You are a weather specialist. Return concise user-ready answers.",
)

calculator_agent = Agent(
    model=worker_model,
    deps_type=AgentDeps,
    output_type=str,
    system_prompt="You are a calculation specialist. Return concise correct answers.",
)

research_agent = Agent(
    model=worker_model,
    deps_type=AgentDeps,
    output_type=str,
    system_prompt="You are a research specialist. Return concise answers with useful links when available.",
)


@weather_agent.tool
async def get_weather_data(ctx: RunContext[AgentDeps], city: str) -> dict:
    return await get_weather(city)


@calculator_agent.tool
async def run_calculation(ctx: RunContext[AgentDeps], expression: str) -> dict:
    return await calculate_expression(expression)


@research_agent.tool
async def run_web_search(ctx: RunContext[AgentDeps], query: str) -> dict:
    return await web_search(query)
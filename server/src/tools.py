import ast
import math
import operator
import os


import httpx
from sympy import sympify


SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
}

def _safe_eval(node):
    if isinstance(node, ast.Num):
        return node.n
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp):
        left = _safe_eval(node.left)
        right = _safe_eval(node.right)
        op_type = type(node.op)
        if op_type not in SAFE_OPERATORS:
            raise ValueError("Unsupported operator")
        return SAFE_OPERATORS[op_type](left, right)
    if isinstance(node, ast.UnaryOp):
        operand = _safe_eval(node.operand)
        op_type = type(node.op)
        if op_type not in SAFE_OPERATORS:
            raise ValueError("Unsupported unary operator")
        return SAFE_OPERATORS[op_type](operand)
    raise ValueError("Unsafe expression")


async def calculate_expression(expression: str) -> dict:
    """
    Safely evaluate arithmetic. Falls back to sympy for slightly more complex math.
    """
    try:
        tree = ast.parse(expression, mode="eval")
        result = _safe_eval(tree.body)
        return {
            "tool": "calculate_expression",
            "expression": expression,
            "result": str(result),
            "mode": "safe_ast",
        }
    except Exception:
        try:
            result = sympify(expression)
            return {
                "tool": "calculate_expression",
                "expression": expression,
                "result": str(result),
                "mode": "sympy",
            }
        except Exception as e:
            return {
                "tool": "calculate_expression",
                "expression": expression,
                "error": f"Could not calculate expression: {e}",
            }


async def get_weather(city: str) -> dict:
    """
    Get current weather using wttr.in
    """
    async with httpx.AsyncClient(timeout=15.0) as client:
        res = await client.get(f"https://wttr.in/{city}?format=j1")
        res.raise_for_status()
        data = res.json()
        current = data["current_condition"][0]

        return {
            "tool": "get_weather",
            "city": city,
            "temp_c": current["temp_C"],
            "temp_f": current["temp_F"],
            "description": current["weatherDesc"][0]["value"],
            "humidity": current["humidity"],
            "wind_kmph": current["windspeedKmph"],
        }


async def web_search(query: str) -> dict:
    """
    Minimal Tavily web search wrapper.
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return {
            "tool": "web_search",
            "query": query,
            "error": "TAVILY_API_KEY not configured",
        }

    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "advanced",
        "max_results": 5,
        "include_answer": True,
    }

    async with httpx.AsyncClient(timeout=25.0) as client:
        res = await client.post("https://api.tavily.com/search", json=payload)
        res.raise_for_status()
        data = res.json()

        results = []
        for item in data.get("results", [])[:5]:
            results.append(
                {
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "content": item.get("content"),
                }
            )

        return {
            "tool": "web_search",
            "query": query,
            "answer": data.get("answer"),
            "results": results,
        }
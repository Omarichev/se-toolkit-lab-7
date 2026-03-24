"""LLM client for intent-based routing.

Handles communication with the LLM API using OpenAI-compatible interface.
Supports tool calling for routing user queries to backend API endpoints.
"""

import json
import sys
from typing import Any

import httpx


def get_tool_definitions() -> list[dict[str, Any]]:
    """Return the list of tool definitions for the LLM.

    Each tool corresponds to a backend API endpoint.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "get_items",
                "description": "Get the list of all labs and tasks available in the system",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_learners",
                "description": "Get the list of enrolled learners with their group assignments",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_scores",
                "description": "Get score distribution (4 buckets) for a specific lab",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lab": {
                            "type": "string",
                            "description": "Lab identifier, e.g. 'lab-01', 'lab-04'",
                        }
                    },
                    "required": ["lab"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_pass_rates",
                "description": "Get per-task average pass rates and attempt counts for a lab",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lab": {
                            "type": "string",
                            "description": "Lab identifier, e.g. 'lab-01', 'lab-04'",
                        }
                    },
                    "required": ["lab"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_timeline",
                "description": "Get submission timeline showing submissions per day for a lab",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lab": {
                            "type": "string",
                            "description": "Lab identifier, e.g. 'lab-01', 'lab-04'",
                        }
                    },
                    "required": ["lab"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_groups",
                "description": "Get per-group average scores and student counts for a lab",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lab": {
                            "type": "string",
                            "description": "Lab identifier, e.g. 'lab-01', 'lab-04'",
                        }
                    },
                    "required": ["lab"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_top_learners",
                "description": "Get top N learners ranked by score for a specific lab",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lab": {
                            "type": "string",
                            "description": "Lab identifier, e.g. 'lab-01', 'lab-04'",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of top learners to return, e.g. 5, 10",
                            "default": 10,
                        },
                    },
                    "required": ["lab"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_completion_rate",
                "description": "Get the completion rate percentage for a specific lab",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "lab": {
                            "type": "string",
                            "description": "Lab identifier, e.g. 'lab-01', 'lab-04'",
                        }
                    },
                    "required": ["lab"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "trigger_sync",
                "description": "Trigger a data sync to refresh data from the autochecker",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        },
    ]


def get_system_prompt() -> str:
    """Return the system prompt that guides the LLM's behavior.

    The prompt encourages tool use and explains how to handle different scenarios.
    """
    return """You are a helpful assistant for a learning management system. You have access to tools that fetch data from the backend API.

Your job is to:
1. Understand what the user is asking
2. Decide which tool(s) to call to get the information
3. After receiving tool results, synthesize a clear, helpful answer

Tool use guidelines:
- Always use tools to get real data before answering questions about labs, scores, learners, etc.
- For comparison questions (e.g., "which lab has the lowest"), first get the list of items, then call the relevant tool for each item.
- For questions about a specific lab, use the lab identifier exactly as it appears (e.g., "lab-01", "lab-04").
- If the user's message is a greeting, respond warmly and mention what you can help with.
- If the user's message is unclear or seems like gibberish, politely ask for clarification and suggest what kinds of questions you can answer.

Available tools:
- get_items: List all labs and tasks
- get_learners: List all enrolled students
- get_scores: Score distribution for a lab
- get_pass_rates: Pass rates per task in a lab
- get_timeline: Submission timeline for a lab
- get_groups: Group performance in a lab
- get_top_learners: Top students in a lab
- get_completion_rate: Completion percentage for a lab
- trigger_sync: Refresh data from autochecker

When you need data, call the appropriate tool. After receiving results, provide a clear summary to the user."""


async def call_llm(
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
    config: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Call the LLM API with the given messages and tools.

    Args:
        messages: List of message dicts with 'role' and 'content' keys
        tools: Optional list of tool definitions
        config: Optional config dict with LLM_API_KEY, LLM_API_BASE_URL, LLM_API_MODEL

    Returns:
        The LLM response dict, which may contain:
        - content: str (text response)
        - tool_calls: list of tool call dicts
    """
    # Import config - handle both 'config' and 'bot.config' paths
    if config is None:
        try:
            from bot.config import load_config
        except ImportError:
            from config import load_config
        config = load_config()

    api_key = config.get("LLM_API_KEY", "")
    base_url = config.get("LLM_API_BASE_URL", "http://localhost:42005/v1")
    model = config.get("LLM_API_MODEL", "coder-model")

    if not api_key:
        return {"content": "LLM API key not configured. Please set LLM_API_KEY in .env.bot.secret"}

    # Ensure base_url ends with /v1 or adjust for chat/completions endpoint
    if not base_url.endswith("/v1") and not base_url.endswith("/chat/completions"):
        base_url = base_url.rstrip("/") + "/v1"

    endpoint = base_url.rstrip("/") + "/chat/completions"

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
    }

    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                endpoint,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            # Extract the assistant message
            choice = data.get("choices", [{}])[0]
            message = choice.get("message", {})

            return message

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                return {
                    "content": "LLM authentication failed (HTTP 401). Your API token may have expired. Try: cd ~/qwen-code-oai-proxy && docker compose restart"
                }
            return {"content": f"LLM error: HTTP {e.response.status_code}"}
        except httpx.ConnectError:
            return {"content": "LLM service unreachable. Make sure the LLM proxy is running."}
        except Exception as e:
            return {"content": f"LLM error: {type(e).__name__}: {str(e)}"}


async def route(
    user_message: str,
    tools: dict[str, callable],
    config: dict[str, str] | None = None,
    debug: bool = True,
) -> str:
    """Route a user message through the LLM tool-calling loop.

    This is the main intent routing function:
    1. Send user message + tool definitions to LLM
    2. LLM returns tool calls
    3. Execute tools, feed results back
    4. LLM produces final answer
    5. Return the answer

    Args:
        user_message: The user's plain text message
        tools: Dict mapping tool names to callable functions
        config: Optional config dict
        debug: If True, print debug info to stderr

    Returns:
        The final response string to show to the user
    """
    # Initialize conversation with system prompt
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": get_system_prompt()},
        {"role": "user", "content": user_message},
    ]

    tool_definitions = get_tool_definitions()

    max_iterations = 5  # Prevent infinite loops
    iteration = 0

    while iteration < max_iterations:
        iteration += 1

        # Call LLM
        response = await call_llm(messages, tool_definitions, config)

        # Check for tool calls
        tool_calls = response.get("tool_calls", [])

        if not tool_calls:
            # No tool calls - LLM is giving final answer
            content = response.get("content", "No response from LLM")
            return content

        # Execute tool calls
        tool_results = []
        for tool_call in tool_calls:
            function = tool_call.get("function", {})
            tool_name = function.get("name", "")
            args_str = function.get("arguments", "{}")

            try:
                args = json.loads(args_str) if args_str else {}
            except json.JSONDecodeError:
                args = {}

            if debug:
                print(f"[tool] LLM called: {tool_name}({args})", file=sys.stderr)

            # Execute the tool
            tool_func = tools.get(tool_name)
            if tool_func:
                try:
                    result = await tool_func(**args)
                    # Convert result to string for LLM
                    result_str = json.dumps(result) if isinstance(result, (dict, list)) else str(result)
                except Exception as e:
                    result_str = f"Error: {type(e).__name__}: {str(e)}"
            else:
                result_str = f"Error: Unknown tool '{tool_name}'"

            if debug:
                # Show abbreviated result
                preview = result_str[:100] + "..." if len(result_str) > 100 else result_str
                print(f"[tool] Result: {preview}", file=sys.stderr)

            tool_results.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.get("id", ""),
                    "content": result_str,
                }
            )

        # Add assistant message with tool calls to conversation
        messages.append(
            {
                "role": "assistant",
                "content": response.get("content"),
                "tool_calls": tool_calls,
            }
        )

        # Add tool results to conversation
        messages.extend(tool_results)

        if debug:
            print(f"[summary] Feeding {len(tool_results)} tool result(s) back to LLM", file=sys.stderr)

    # If we hit max iterations, return what we have
    return "I'm still working on that. Let me summarize what I found so far: " + response.get(
        "content", "Please try rephrasing your question."
    )

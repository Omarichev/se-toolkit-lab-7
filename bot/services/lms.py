"""LMS API client for fetching data from the backend.

All HTTP calls to the LMS backend go through this module.
Handles errors gracefully and returns user-friendly messages.
"""

import httpx


def get_api_client() -> httpx.AsyncClient:
    """Create an async HTTP client with LMS API headers.

    Returns:
        An async httpx.Client configured with the LMS API URL and auth header
    """
    import os
    from pathlib import Path
    from dotenv import load_dotenv

    # Load env vars from .env.bot.secret
    bot_dir = Path(__file__).parent.parent
    env_file = bot_dir / ".env.bot.secret"
    if env_file.exists():
        load_dotenv(env_file)

    api_url = os.getenv("LMS_API_URL", "http://localhost:42002")
    api_key = os.getenv("LMS_API_KEY", "my-secret-api-key")

    return httpx.AsyncClient(
        base_url=api_url,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=10.0,
    )


async def get_items() -> dict:
    """Fetch all items (labs and tasks) from the backend.

    Returns:
        Dict with keys:
            - success: bool
            - items: list of item dicts (if successful)
            - message: str (user-friendly response or error)
    """
    try:
        async with get_api_client() as client:
            response = await client.get("/items/")
            response.raise_for_status()
            items = response.json()

            return {
                "success": True,
                "items": items,
                "message": f"Total items: {len(items)}",
            }

    except httpx.ConnectError as e:
        return {
            "success": False,
            "items": [],
            "message": f"Backend error: connection refused.",
        }
    except httpx.HTTPStatusError as e:
        return {
            "success": False,
            "items": [],
            "message": f"Backend error: HTTP {e.response.status_code}.",
        }
    except httpx.HTTPError as e:
        return {
            "success": False,
            "items": [],
            "message": f"Backend error: {type(e).__name__}. {str(e)}",
        }
    except Exception as e:
        return {
            "success": False,
            "items": [],
            "message": f"Backend error: {type(e).__name__}. {str(e)}",
        }


async def check_health() -> dict:
    """Check if the backend is healthy.

    Returns:
        Dict with keys:
            - healthy: bool
            - message: str (user-friendly status)
            - item_count: int (if healthy)
            - error: str (if unhealthy)
    """
    try:
        async with get_api_client() as client:
            response = await client.get("/items/")
            response.raise_for_status()
            items = response.json()
            return {
                "healthy": True,
                "message": f"Backend is healthy. {len(items)} items available.",
                "item_count": len(items),
            }
    except httpx.ConnectError as e:
        return {
            "healthy": False,
            "message": f"Backend error: connection refused. Check that the services are running.",
            "error": str(e),
        }
    except httpx.HTTPStatusError as e:
        return {
            "healthy": False,
            "message": f"Backend error: HTTP {e.response.status_code} {e.response.reason_phrase}. The backend service may be down.",
            "error": str(e),
        }
    except httpx.HTTPError as e:
        return {
            "healthy": False,
            "message": f"Backend error: {type(e).__name__}. {str(e)}",
            "error": str(e),
        }
    except Exception as e:
        return {
            "healthy": False,
            "message": f"Backend error: {type(e).__name__}. {str(e)}",
            "error": str(e),
        }


async def get_labs() -> dict:
    """Fetch all labs from the backend.

    Returns:
        Dict with keys:
            - success: bool
            - labs: list of lab dicts (if successful)
            - message: str (user-friendly response or error)
    """
    result = await get_items()
    if not result["success"]:
        return {
            "success": False,
            "labs": [],
            "message": result["message"],
        }

    # Filter for labs only (type == "lab")
    items = result.get("items", [])
    labs = [item for item in items if item.get("type") == "lab"]

    if not labs:
        return {
            "success": True,
            "labs": [],
            "message": "No labs available.",
        }

    # Format lab list
    lab_lines = []
    for lab in labs:
        lab_id = lab.get("id", "?")
        lab_title = lab.get("title", f"Lab {lab_id}")
        lab_lines.append(f"- {lab_title}")

    return {
        "success": True,
        "labs": labs,
        "message": "Available labs:\n" + "\n".join(lab_lines),
    }


async def get_pass_rates(lab: str) -> dict:
    """Fetch pass rates for a specific lab.

    Args:
        lab: Lab identifier (e.g., "lab-04")

    Returns:
        Dict with keys:
            - success: bool
            - pass_rates: list of pass rate dicts (if successful)
            - message: str (user-friendly formatted response or error)
    """
    if not lab:
        return {
            "success": False,
            "pass_rates": [],
            "message": "Please specify a lab, e.g., /scores lab-04",
        }

    try:
        async with get_api_client() as client:
            response = await client.get("/analytics/pass-rates", params={"lab": lab})
            response.raise_for_status()
            data = response.json()

            if not data:
                return {
                    "success": True,
                    "pass_rates": [],
                    "message": f"No pass rate data available for {lab}.",
                }

            # Format pass rates
            # Expected format: [{"task": "Task Name", "pass_rate": 0.75, "attempts": 100}, ...]
            lines = [f"Pass rates for {lab}:"]
            for rate in data:
                task_name = rate.get("task", "Unknown task")
                pass_rate = rate.get("pass_rate", 0)
                attempts = rate.get("attempts", 0)
                percentage = pass_rate * 100
                lines.append(f"- {task_name}: {percentage:.1f}% ({attempts} attempts)")

            return {
                "success": True,
                "pass_rates": data,
                "message": "\n".join(lines),
            }

    except httpx.ConnectError as e:
        return {
            "success": False,
            "pass_rates": [],
            "message": f"Backend error: connection refused. Check that the services are running.",
        }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {
                "success": False,
                "pass_rates": [],
                "message": f"Lab '{lab}' not found. Use /labs to see available labs.",
            }
        return {
            "success": False,
            "pass_rates": [],
            "message": f"Backend error: HTTP {e.response.status_code} {e.response.reason_phrase}.",
        }
    except httpx.HTTPError as e:
        return {
            "success": False,
            "pass_rates": [],
            "message": f"Backend error: {type(e).__name__}. {str(e)}",
        }
    except Exception as e:
        return {
            "success": False,
            "pass_rates": [],
            "message": f"Backend error: {type(e).__name__}. {str(e)}",
        }


async def get_learners() -> dict:
    """Fetch all enrolled learners from the backend.

    Returns:
        Dict with keys:
            - success: bool
            - learners: list of learner dicts (if successful)
            - message: str (user-friendly response or error)
    """
    try:
        async with get_api_client() as client:
            response = await client.get("/learners/")
            response.raise_for_status()
            learners = response.json()

            if not learners:
                return {
                    "success": True,
                    "learners": [],
                    "message": "No learners enrolled yet.",
                }

            return {
                "success": True,
                "learners": learners,
                "message": f"Total learners: {len(learners)}",
            }

    except httpx.ConnectError as e:
        return {
            "success": False,
            "learners": [],
            "message": f"Backend error: connection refused.",
        }
    except httpx.HTTPStatusError as e:
        return {
            "success": False,
            "learners": [],
            "message": f"Backend error: HTTP {e.response.status_code}.",
        }
    except httpx.HTTPError as e:
        return {
            "success": False,
            "learners": [],
            "message": f"Backend error: {type(e).__name__}. {str(e)}",
        }
    except Exception as e:
        return {
            "success": False,
            "learners": [],
            "message": f"Backend error: {type(e).__name__}. {str(e)}",
        }


async def get_scores(lab: str) -> dict:
    """Fetch score distribution for a specific lab.

    Args:
        lab: Lab identifier (e.g., "lab-04")

    Returns:
        Dict with keys:
            - success: bool
            - scores: list of score bucket dicts (if successful)
            - message: str (user-friendly formatted response or error)
    """
    if not lab:
        return {
            "success": False,
            "scores": [],
            "message": "Please specify a lab, e.g., get_scores(lab='lab-04')",
        }

    try:
        async with get_api_client() as client:
            response = await client.get("/analytics/scores", params={"lab": lab})
            response.raise_for_status()
            data = response.json()

            if not data:
                return {
                    "success": True,
                    "scores": [],
                    "message": f"No score data available for {lab}.",
                }

            # Format score distribution
            lines = [f"Score distribution for {lab}:"]
            for bucket in data:
                range_label = bucket.get("range", "Unknown")
                count = bucket.get("count", 0)
                lines.append(f"- {range_label}: {count} students")

            return {
                "success": True,
                "scores": data,
                "message": "\n".join(lines),
            }

    except httpx.ConnectError as e:
        return {
            "success": False,
            "scores": [],
            "message": f"Backend error: connection refused.",
        }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {
                "success": False,
                "scores": [],
                "message": f"Lab '{lab}' not found.",
            }
        return {
            "success": False,
            "scores": [],
            "message": f"Backend error: HTTP {e.response.status_code}.",
        }
    except httpx.HTTPError as e:
        return {
            "success": False,
            "scores": [],
            "message": f"Backend error: {type(e).__name__}. {str(e)}",
        }
    except Exception as e:
        return {
            "success": False,
            "scores": [],
            "message": f"Backend error: {type(e).__name__}. {str(e)}",
        }


async def get_timeline(lab: str) -> dict:
    """Fetch submission timeline for a specific lab.

    Args:
        lab: Lab identifier (e.g., "lab-04")

    Returns:
        Dict with keys:
            - success: bool
            - timeline: list of timeline dicts (if successful)
            - message: str (user-friendly formatted response or error)
    """
    if not lab:
        return {
            "success": False,
            "timeline": [],
            "message": "Please specify a lab, e.g., get_timeline(lab='lab-04')",
        }

    try:
        async with get_api_client() as client:
            response = await client.get("/analytics/timeline", params={"lab": lab})
            response.raise_for_status()
            data = response.json()

            if not data:
                return {
                    "success": True,
                    "timeline": [],
                    "message": f"No timeline data available for {lab}.",
                }

            # Format timeline
            lines = [f"Submission timeline for {lab}:"]
            for entry in data:
                date = entry.get("date", "Unknown")
                count = entry.get("count", 0)
                lines.append(f"- {date}: {count} submissions")

            return {
                "success": True,
                "timeline": data,
                "message": "\n".join(lines),
            }

    except httpx.ConnectError as e:
        return {
            "success": False,
            "timeline": [],
            "message": f"Backend error: connection refused.",
        }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {
                "success": False,
                "timeline": [],
                "message": f"Lab '{lab}' not found.",
            }
        return {
            "success": False,
            "timeline": [],
            "message": f"Backend error: HTTP {e.response.status_code}.",
        }
    except httpx.HTTPError as e:
        return {
            "success": False,
            "timeline": [],
            "message": f"Backend error: {type(e).__name__}. {str(e)}",
        }
    except Exception as e:
        return {
            "success": False,
            "timeline": [],
            "message": f"Backend error: {type(e).__name__}. {str(e)}",
        }


async def get_groups(lab: str) -> dict:
    """Fetch per-group performance for a specific lab.

    Args:
        lab: Lab identifier (e.g., "lab-04")

    Returns:
        Dict with keys:
            - success: bool
            - groups: list of group dicts (if successful)
            - message: str (user-friendly formatted response or error)
    """
    if not lab:
        return {
            "success": False,
            "groups": [],
            "message": "Please specify a lab, e.g., get_groups(lab='lab-04')",
        }

    try:
        async with get_api_client() as client:
            response = await client.get("/analytics/groups", params={"lab": lab})
            response.raise_for_status()
            data = response.json()

            if not data:
                return {
                    "success": True,
                    "groups": [],
                    "message": f"No group data available for {lab}.",
                }

            # Format groups - sort by average score descending
            sorted_groups = sorted(data, key=lambda g: g.get("average_score", 0), reverse=True)
            lines = [f"Group performance for {lab}:"]
            for i, group in enumerate(sorted_groups, 1):
                name = group.get("group", "Unknown")
                avg = group.get("average_score", 0) * 100
                students = group.get("student_count", 0)
                lines.append(f"{i}. {name}: {avg:.1f}% avg ({students} students)")

            return {
                "success": True,
                "groups": data,
                "message": "\n".join(lines),
            }

    except httpx.ConnectError as e:
        return {
            "success": False,
            "groups": [],
            "message": f"Backend error: connection refused.",
        }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {
                "success": False,
                "groups": [],
                "message": f"Lab '{lab}' not found.",
            }
        return {
            "success": False,
            "groups": [],
            "message": f"Backend error: HTTP {e.response.status_code}.",
        }
    except httpx.HTTPError as e:
        return {
            "success": False,
            "groups": [],
            "message": f"Backend error: {type(e).__name__}. {str(e)}",
        }
    except Exception as e:
        return {
            "success": False,
            "groups": [],
            "message": f"Backend error: {type(e).__name__}. {str(e)}",
        }


async def get_top_learners(lab: str, limit: int = 10) -> dict:
    """Fetch top learners for a specific lab.

    Args:
        lab: Lab identifier (e.g., "lab-04")
        limit: Number of top learners to return (default: 10)

    Returns:
        Dict with keys:
            - success: bool
            - top_learners: list of learner dicts (if successful)
            - message: str (user-friendly formatted response or error)
    """
    if not lab:
        return {
            "success": False,
            "top_learners": [],
            "message": "Please specify a lab, e.g., get_top_learners(lab='lab-04')",
        }

    try:
        async with get_api_client() as client:
            response = await client.get(
                "/analytics/top-learners", params={"lab": lab, "limit": limit}
            )
            response.raise_for_status()
            data = response.json()

            if not data:
                return {
                    "success": True,
                    "top_learners": [],
                    "message": f"No top learners data available for {lab}.",
                }

            # Format leaderboard
            lines = [f"Top {len(data)} learners in {lab}:"]
            for i, learner in enumerate(data, 1):
                name = learner.get("name", learner.get("learner_name", "Unknown"))
                score = learner.get("score", 0) * 100
                lines.append(f"{i}. {name}: {score:.1f}%")

            return {
                "success": True,
                "top_learners": data,
                "message": "\n".join(lines),
            }

    except httpx.ConnectError as e:
        return {
            "success": False,
            "top_learners": [],
            "message": f"Backend error: connection refused.",
        }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {
                "success": False,
                "top_learners": [],
                "message": f"Lab '{lab}' not found.",
            }
        return {
            "success": False,
            "top_learners": [],
            "message": f"Backend error: HTTP {e.response.status_code}.",
        }
    except httpx.HTTPError as e:
        return {
            "success": False,
            "top_learners": [],
            "message": f"Backend error: {type(e).__name__}. {str(e)}",
        }
    except Exception as e:
        return {
            "success": False,
            "top_learners": [],
            "message": f"Backend error: {type(e).__name__}. {str(e)}",
        }


async def get_completion_rate(lab: str) -> dict:
    """Fetch completion rate for a specific lab.

    Args:
        lab: Lab identifier (e.g., "lab-04")

    Returns:
        Dict with keys:
            - success: bool
            - completion_rate: float (if successful)
            - message: str (user-friendly formatted response or error)
    """
    if not lab:
        return {
            "success": False,
            "completion_rate": 0.0,
            "message": "Please specify a lab, e.g., get_completion_rate(lab='lab-04')",
        }

    try:
        async with get_api_client() as client:
            response = await client.get("/analytics/completion-rate", params={"lab": lab})
            response.raise_for_status()
            data = response.json()

            # Handle both dict and float responses
            if isinstance(data, dict):
                rate = data.get("completion_rate", data.get("rate", 0))
            else:
                rate = data

            percentage = rate * 100 if isinstance(rate, (int, float)) else 0

            return {
                "success": True,
                "completion_rate": rate,
                "message": f"Completion rate for {lab}: {percentage:.1f}%",
            }

    except httpx.ConnectError as e:
        return {
            "success": False,
            "completion_rate": 0.0,
            "message": f"Backend error: connection refused.",
        }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return {
                "success": False,
                "completion_rate": 0.0,
                "message": f"Lab '{lab}' not found.",
            }
        return {
            "success": False,
            "completion_rate": 0.0,
            "message": f"Backend error: HTTP {e.response.status_code}.",
        }
    except httpx.HTTPError as e:
        return {
            "success": False,
            "completion_rate": 0.0,
            "message": f"Backend error: {type(e).__name__}. {str(e)}",
        }
    except Exception as e:
        return {
            "success": False,
            "completion_rate": 0.0,
            "message": f"Backend error: {type(e).__name__}. {str(e)}",
        }


async def trigger_sync() -> dict:
    """Trigger a data sync from the autochecker.

    Returns:
        Dict with keys:
            - success: bool
            - message: str (user-friendly response or error)
    """
    try:
        async with get_api_client() as client:
            response = await client.post("/pipeline/sync")
            response.raise_for_status()
            data = response.json()

            return {
                "success": True,
                "message": "Data sync triggered successfully. Check back in a few moments.",
            }

    except httpx.ConnectError as e:
        return {
            "success": False,
            "message": f"Backend error: connection refused.",
        }
    except httpx.HTTPStatusError as e:
        return {
            "success": False,
            "message": f"Backend error: HTTP {e.response.status_code}.",
        }
    except httpx.HTTPError as e:
        return {
            "success": False,
            "message": f"Backend error: {type(e).__name__}. {str(e)}",
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Backend error: {type(e).__name__}. {str(e)}",
        }

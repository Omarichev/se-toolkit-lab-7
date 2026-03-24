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
    try:
        async with get_api_client() as client:
            response = await client.get("/items/")
            response.raise_for_status()
            items = response.json()

            # Filter for labs only (type == "lab")
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

    except httpx.ConnectError as e:
        return {
            "success": False,
            "labs": [],
            "message": f"Backend error: connection refused. Check that the services are running.",
        }
    except httpx.HTTPStatusError as e:
        return {
            "success": False,
            "labs": [],
            "message": f"Backend error: HTTP {e.response.status_code} {e.response.reason_phrase}. The backend service may be down.",
        }
    except httpx.HTTPError as e:
        return {
            "success": False,
            "labs": [],
            "message": f"Backend error: {type(e).__name__}. {str(e)}",
        }
    except Exception as e:
        return {
            "success": False,
            "labs": [],
            "message": f"Backend error: {type(e).__name__}. {str(e)}",
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

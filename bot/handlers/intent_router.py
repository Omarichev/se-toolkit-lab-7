"""Intent-based router for plain text messages.

Uses LLM to interpret user messages and route to appropriate API tools.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports when running from bot/
bot_dir = Path(__file__).parent.parent
if str(bot_dir) not in sys.path:
    sys.path.insert(0, str(bot_dir))

from services.llm_client import route as llm_route
from services.lms import (
    get_items,
    get_learners,
    get_scores,
    get_pass_rates,
    get_timeline,
    get_groups,
    get_top_learners,
    get_completion_rate,
    trigger_sync,
)


# Map tool names (from LLM) to actual functions
TOOLS = {
    "get_items": get_items,
    "get_learners": get_learners,
    "get_scores": get_scores,
    "get_pass_rates": get_pass_rates,
    "get_timeline": get_timeline,
    "get_groups": get_groups,
    "get_top_learners": get_top_learners,
    "get_completion_rate": get_completion_rate,
    "trigger_sync": trigger_sync,
}


async def handle_intent(message: str, config: dict | None = None) -> str:
    """Handle a plain text message using LLM-based intent routing.

    Args:
        message: The user's plain text message
        config: Optional config dict with LLM settings

    Returns:
        The response text to show to the user
    """
    return await llm_route(message, TOOLS, config, debug=True)

"""Command handlers for slash commands.

Each handler is a function that takes arguments and returns a string response.
"""

from services.lms import check_health, get_labs, get_pass_rates


async def handle_start(args: str) -> str:
    """Handle /start command.

    Args:
        args: Any arguments passed after the command (unused for /start)

    Returns:
        Welcome message
    """
    return "Welcome to the SE Toolkit Bot! 🤖\n\nUse /help to see available commands."


async def handle_help(args: str) -> str:
    """Handle /help command.

    Args:
        args: Any arguments passed after the command (unused for /help)

    Returns:
        List of available commands
    """
    return """Available commands:

/start - Welcome message
/help - Show this help message
/health - Check backend status
/labs - List available labs
/scores <lab> - Show scores for a specific lab

You can also ask questions in plain language!"""


async def handle_health(args: str) -> str:
    """Handle /health command.

    Args:
        args: Any arguments passed after the command (unused for /health)

    Returns:
        Backend health status
    """
    result = await check_health()
    return result["message"]


async def handle_labs(args: str) -> str:
    """Handle /labs command.

    Args:
        args: Any arguments passed after the command (unused for /labs)

    Returns:
        List of available labs
    """
    result = await get_labs()
    return result["message"]


async def handle_scores(args: str) -> str:
    """Handle /scores command.

    Args:
        args: Lab name or ID (e.g., "lab-04")

    Returns:
        Scores for the specified lab
    """
    if not args:
        return "Please specify a lab, e.g., /scores lab-04"

    result = await get_pass_rates(args)
    return result["message"]

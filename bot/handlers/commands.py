"""Command handlers for slash commands.

Each handler is a function that takes arguments and returns a string response.
For Telegram mode, handlers also return inline keyboard markup.
"""

from services.lms import check_health, get_labs, get_pass_rates


# Inline keyboard markup for common actions
# These are aiogram InlineKeyboardMarkup definitions
# Format: {"text": "Button Label", "callback_data": "action"}

START_KEYBOARD = {
    "inline_keyboard": [
        [
            {"text": "📋 List Labs", "callback_data": "cmd_labs"},
            {"text": "🏥 Health Check", "callback_data": "cmd_health"},
        ],
        [
            {"text": "📊 Score Distribution", "callback_data": "prompt_scores"},
            {"text": "🏆 Top Learners", "callback_data": "prompt_top"},
        ],
        [
            {"text": "❓ Help", "callback_data": "cmd_help"},
        ],
    ]
}

HELP_KEYBOARD = {
    "inline_keyboard": [
        [
            {"text": "📋 View Labs", "callback_data": "cmd_labs"},
            {"text": "📊 Scores for Lab", "callback_data": "prompt_scores"},
        ],
        [
            {"text": "🏆 Top Learners", "callback_data": "prompt_top"},
            {"text": "👥 Group Performance", "callback_data": "prompt_groups"},
        ],
        [
            {"text": "📈 Completion Rate", "callback_data": "prompt_completion"},
            {"text": "🕐 Timeline", "callback_data": "prompt_timeline"},
        ],
    ]
}


def get_start_keyboard() -> dict:
    """Get the inline keyboard markup for /start command.

    Returns:
        Dict suitable for aiogram's reply_markup parameter
    """
    return START_KEYBOARD


def get_help_keyboard() -> dict:
    """Get the inline keyboard markup for /help command.

    Returns:
        Dict suitable for aiogram's reply_markup parameter
    """
    return HELP_KEYBOARD


async def handle_start(args: str) -> str:
    """Handle /start command.

    Args:
        args: Any arguments passed after the command (unused for /start)

    Returns:
        Welcome message
    """
    return """Welcome to the SE Toolkit Bot! 🤖

I'm your assistant for the learning management system. I can help you with:

• Viewing labs and tasks
• Checking scores and pass rates
• Finding top performers
• Comparing group performance
• Tracking completion rates
• Viewing submission timelines

You can:
1. Use slash commands like /help, /labs, /scores
2. Ask questions in plain language like:
   - "What labs are available?"
   - "Show me scores for lab 4"
   - "Which lab has the lowest pass rate?"
   - "Who are the top 5 students?"

Use the buttons below for quick actions!"""


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

Example queries you can ask in plain language:
• "What labs are available?"
• "Show me scores for lab 4"
• "Who are the top 5 students in lab 4?"
• "Which lab has the lowest pass rate?"
• "Compare group A and group B"
• "How many students are enrolled?"

Use the buttons below for quick actions!"""


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

"""Command handlers for slash commands.

Each handler is a function that takes arguments and returns a string response.
"""


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
    # TODO: Call backend API to check health
    return "Backend status: OK (placeholder)"


async def handle_labs(args: str) -> str:
    """Handle /labs command.
    
    Args:
        args: Any arguments passed after the command (unused for /labs)
    
    Returns:
        List of available labs
    """
    # TODO: Call backend API to fetch labs
    return "Available labs:\n- Lab 01\n- Lab 02\n- Lab 03\n(placeholder)"


async def handle_scores(args: str) -> str:
    """Handle /scores command.
    
    Args:
        args: Lab name or ID (e.g., "lab-04")
    
    Returns:
        Scores for the specified lab
    """
    if not args:
        return "Please specify a lab, e.g., /scores lab-04"
    
    # TODO: Call backend API to fetch scores
    return f"Scores for {args}:\n- Task 1: 80%\n- Task 2: 75%\n(placeholder)"

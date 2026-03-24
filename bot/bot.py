#!/usr/bin/env python3
"""Telegram bot entry point with --test mode.

Usage:
    uv run bot.py --test "/start"     # Test mode, no Telegram connection
    uv run bot.py                     # Normal mode, connects to Telegram
"""

import asyncio
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, CommandStart
from config import load_config
from handlers.commands import (
    handle_start,
    handle_help,
    handle_health,
    handle_labs,
    handle_scores,
)
from handlers.intent_router import handle_intent


# Command router - maps command names to handler functions
COMMAND_HANDLERS = {
    "start": handle_start,
    "help": handle_help,
    "health": handle_health,
    "labs": handle_labs,
    "scores": handle_scores,
}


async def process_command(command: str) -> str:
    """Process a command string and return the response.

    Args:
        command: The full command string, e.g., "/start" or "/scores lab-04"
            or plain text like "what labs are available"

    Returns:
        The response text from the handler
    """
    # Load config for LLM
    config = load_config()

    # Parse the command
    if not command.startswith("/"):
        # Plain text - route through LLM
        return await handle_intent(command, config)

    # Remove leading slash and split into command + args
    parts = command[1:].split(maxsplit=1)
    cmd_name = parts[0].lower()
    cmd_args = parts[1] if len(parts) > 1 else ""

    # Find and call the handler
    handler = COMMAND_HANDLERS.get(cmd_name)
    if handler:
        return await handler(cmd_args)
    else:
        return f"Unknown command: /{cmd_name}. Use /help to see available commands."


async def run_test_mode(command: str) -> None:
    """Run the bot in test mode - process a single command and exit.
    
    Args:
        command: The command to test, e.g., "/start"
    """
    # Load config (not used in test mode, but validates .env.bot.secret exists)
    config = load_config()
    
    # Process the command
    response = await process_command(command)
    
    # Print response to stdout
    print(response)


async def run_telegram_mode() -> None:
    """Run the bot in normal Telegram mode.

    Connects to Telegram and listens for messages.
    """
    config = load_config()

    if not config["BOT_TOKEN"]:
        print("Error: BOT_TOKEN not set. Please configure .env.bot.secret")
        sys.exit(1)

    # Initialize aiogram bot and dispatcher
    bot = Bot(token=config["BOT_TOKEN"])
    dp = Dispatcher()

    # Register command handlers
    @dp.message(CommandStart())
    async def start_handler(message: types.Message) -> None:
        """Handle /start command."""
        response = await handle_start("")
        await message.answer(response)

    @dp.message(Command("help"))
    async def help_handler(message: types.Message) -> None:
        """Handle /help command."""
        response = await handle_help("")
        await message.answer(response)

    @dp.message(Command("health"))
    async def health_handler(message: types.Message) -> None:
        """Handle /health command."""
        response = await handle_health("")
        await message.answer(response)

    @dp.message(Command("labs"))
    async def labs_handler(message: types.Message) -> None:
        """Handle /labs command."""
        response = await handle_labs("")
        await message.answer(response)

    @dp.message(Command("scores"))
    async def scores_handler(message: types.Message) -> None:
        """Handle /scores command."""
        # Extract lab argument from command
        args = message.text.split(maxsplit=1)
        lab_arg = args[1] if len(args) > 1 else ""
        response = await handle_scores(lab_arg)
        await message.answer(response)

    @dp.message()
    async def text_handler(message: types.Message) -> None:
        """Handle plain text messages via LLM intent routing."""
        if message.text:
            response = await handle_intent(message.text, config)
            await message.answer(response)

    # Start polling
    print("Application started")
    await dp.start_polling(bot)


async def main() -> None:
    """Main entry point."""
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        if len(sys.argv) < 3:
            print("Usage: uv run bot.py --test <command>")
            print("Example: uv run bot.py --test \"/start\"")
            sys.exit(1)
        
        command = sys.argv[2]
        await run_test_mode(command)
    else:
        await run_telegram_mode()


if __name__ == "__main__":
    asyncio.run(main())

# Telegram Bot Implementation Plan

## Overview

This document outlines the implementation plan for building a Telegram bot that lets users interact with the LMS backend through chat. The bot supports slash commands like `/start`, `/help`, `/health`, `/labs`, and `/scores`, as well as plain language questions interpreted by an LLM.

## Architecture

The bot follows a layered architecture with clear separation of concerns:

1. **Entry Point (`bot.py`)**: Handles both `--test` mode for offline testing and normal Telegram mode. Routes commands to appropriate handlers.

2. **Handler Layer (`handlers/`)**: Pure functions that take command arguments and return text responses. They have no dependency on Telegram, making them testable in isolation.

3. **Service Layer (`services/`)**: Contains API clients for external services:
   - `lms_client.py`: HTTP client for the LMS backend API
   - `llm_client.py`: Client for the LLM API used in intent routing

4. **Configuration (`config.py`)**: Loads secrets from `.env.bot.secret` using python-dotenv.

## Task Breakdown

### Task 1: Plan and Scaffold

- Create project structure with `bot/`, `handlers/`, `services/` directories
- Implement `--test` mode for offline verification
- Add placeholder handlers for `/start`, `/help`, `/health`, `/labs`, `/scores`
- Set up `pyproject.toml` with dependencies (aiogram, httpx, python-dotenv)
- Create `.env.bot.secret` configuration file

### Task 2: Backend Integration

- Implement `LMSClient` in `services/lms_client.py` with Bearer token authentication
- Replace placeholder handlers with real API calls:
  - `/health` → `GET /health` endpoint
  - `/labs` → `GET /items?type=lab`
  - `/scores <lab>` → `GET /analytics/{lab_id}`
- Add error handling for network failures and API errors
- Format responses with rich text (bold, lists, code blocks)

### Task 3: Intent-Based Natural Language Routing

- Implement `LLMClient` in `services/llm_client.py`
- Define tool descriptions for all 9 backend endpoints
- Create intent router that uses LLM to decide which tool to call
- Handle plain text queries like "what labs are available" or "show me scores for lab 4"
- Add inline keyboard buttons for common actions

### Task 4: Containerize and Deploy

- Create `Dockerfile` for the bot
- Add bot service to `docker-compose.yml`
- Configure container networking (use service names, not localhost)
- Deploy to VM and verify bot responds in Telegram
- Document deployment process in README

## Testing Strategy

- **Test mode**: `uv run bot.py --test "/command"` for quick verification
- **Unit tests**: Test handlers in isolation with pytest
- **Integration tests**: Test full flow from Telegram message to API response
- **E2E tests**: Deploy bot and verify in real Telegram chat

## Dependencies

- `aiogram`: Async Telegram Bot API framework
- `httpx`: Async HTTP client for API calls
- `python-dotenv`: Load environment variables from `.env.bot.secret`

## Environment Variables

```
BOT_TOKEN=<telegram-bot-token>
LMS_API_URL=http://localhost:42002
LMS_API_KEY=<api-key>
LLM_API_KEY=<llm-api-key>
LLM_API_BASE_URL=http://localhost:42005/v1
LLM_API_MODEL=coder-model
```

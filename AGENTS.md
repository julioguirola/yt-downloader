# yt-downloader — AGENTS.md

## Package management

- **`uv`** is the package manager (not pip/poetry). Install deps: `uv sync`
- Add a dependency: `uv add <package>`
- Run the app: `uv run python main.py`
- Python 3.14, pinned in `.python-version`

## Docker

- `docker compose up -d` starts both services (yt-downloader + minio)
- Requires `BOT_TOKEN` env var (set in `.env` or shell)
- MinIO console at `http://localhost:9001`, API at `:9000`
- Default MinIO creds in `.env` — **never commit `.env`**

## Architecture

- Single-file app: `main.py`
- Entrypoint: `bot.infinity_polling()` — starts a long-running Telegram bot
- `download_video()` uses `yt-dlp` to download + optional audio-only (MP3 via ffmpeg)
- `list_formats()` shows available formats for a URL
- The bot handler currently responds to YouTube URLs but does NOT call `download_video()` yet

## Known gaps (no infra exists)

- No tests, no CI, no linting/formatter/typecheck config
- `download_video()` is never called from the bot handler (handler only sends a confirmation message)
- README is empty

## YouTube cookies (bot detection)

YouTube blocks requests without auth cookies. Export cookies from a logged-in browser:

```bash
# On a machine with a browser logged into YouTube:
yt-dlp --cookies-from-browser chrome --cookies cookies.txt

# Copy to VM and place in ./cookies/cookies.txt (mounted into container)
```

Set `COOKIES_FILE` path or use the default mount in docker-compose (`./cookies/cookies.txt` → `/cookies/cookies.txt`).

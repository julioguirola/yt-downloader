# yt-downloader

Telegram bot that downloads YouTube videos and stores them in MinIO.

## Flow

1. User sends a YouTube URL to the bot
2. Bot replies with available mp4 formats as inline keyboard buttons
3. User selects a format
4. Bot downloads the video (video + best audio) and uploads it to MinIO
5. Bot replies with the upload confirmation (title, size, bucket path)

## Tech

- **Python 3.14** + `uv` as package manager
- **yt-dlp** for downloading from YouTube
- **pyTelegramBotAPI** for the Telegram bot
- **MinIO** for object storage
- **ffmpeg** required for merging video + audio (installed in the Docker image)

## Setup

### Local

```bash
uv sync
export BOT_TOKEN=<your-telegram-bot-token>
export MINIO_ENDPOINT=localhost:9000
export MINIO_ACCESS_KEY=<key>
export MINIO_SECRET_KEY=<key>
uv run python main.py
```

### Docker

Requires a `.env` file with:

```
BOT_TOKEN=<your-telegram-bot-token>
MINIO_ROOT_USER=<minio-user>
MINIO_ROOT_PASSWORD=<minio-password>
```

```bash
docker compose up -d
```

- **MinIO console**: http://localhost:80
- **MinIO API**: http://localhost:9000
- Proxy settings (`HTTP_PROXY`, `HTTPS_PROXY`) are inherited from the host environment automatically.

## Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `BOT_TOKEN` | yes | — | Telegram bot token |
| `MINIO_ENDPOINT` | no | `localhost:9000` | MinIO API endpoint |
| `MINIO_ACCESS_KEY` | no | `minioadmin` | MinIO access key |
| `MINIO_SECRET_KEY` | no | `minioadmin` | MinIO secret key |
| `MINIO_BUCKET` | no | `videos` | MinIO bucket name (created on startup if missing) |
| `HTTP_PROXY` | no | — | Inherited from host |
| `HTTPS_PROXY` | no | — | Inherited from host |

## Architecture

Single-file app (`main.py`):

- `list_formats(url)` — fetches available mp4 formats (no download)
- `download_and_upload(url, format_id, chat_id)` — downloads video + best audio to a temp dir, uploads to MinIO, notifies the chat
- `handle_message` — receives URLs, shows format buttons
- `callback_format` — handles button selection, triggers download
- `pending_urls` — in-memory dict mapping short IDs to URLs (Telegram `callback_data` is limited to 64 bytes)

Entrypoint: `bot.infinity_polling()` — long-running polling with threaded handlers.

import os
import sys
import tempfile
from yt_dlp import YoutubeDL
import telebot
from telebot import types
from minio import Minio

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY")
MINIO_BUCKET = os.getenv("MINIO_BUCKET")
COOKIES_FILE = os.getenv("COOKIES_FILE")

minio_client = Minio(
    MINIO_ENDPOINT.replace("http://", "").replace("https://", ""),
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=MINIO_ENDPOINT.startswith("https"),
)


def ensure_bucket():
    if not minio_client.bucket_exists(MINIO_BUCKET):
        minio_client.make_bucket(MINIO_BUCKET)


def base_opts():
    opts = {}
    if COOKIES_FILE:
        opts["cookiefile"] = COOKIES_FILE
    return opts


def list_formats(url):
    ydl_opts = base_opts() | {"quiet": True}
    with YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            formats = info.get("formats", [])
            title = info.get("title", "Unknown")
            mp4_formats = [
                {
                    "format_id": f.get("format_id"),
                    "ext": f.get("ext"),
                    "resolution": f.get("resolution"),
                    "note": f.get("format_note", ""),
                    "filesize": f.get("filesize"),
                }
                for f in formats
                if f.get("ext") == "mp4" and f.get("vcodec") != "none"
            ]
            return title, mp4_formats
        except Exception as e:
            return None, []


def download_and_upload(url, format_id, chat_id):
    with tempfile.TemporaryDirectory() as tmpdir:
        ydl_opts = base_opts() | {
            "outtmpl": f"{tmpdir}/%(title)s.%(ext)s",
            "format": format_id,
            "quiet": True,
            "no_warnings": True,
        }
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filepath = ydl.prepare_filename(info)
                if not os.path.exists(filepath):
                    for f in os.listdir(tmpdir):
                        filepath = os.path.join(tmpdir, f)
                        break

            title = info.get("title", "video")
            ext = info.get("ext", "mp4")
            object_name = f"{title}.{ext}"

            file_size = os.path.getsize(filepath)
            minio_client.fput_object(
                MINIO_BUCKET,
                object_name,
                filepath,
                content_type=f"video/{ext}",
            )

            bot.send_message(
                chat_id,
                f"Uploaded: {title}\n"
                f"Size: {file_size / 1024 / 1024:.1f}MB\n"
                f"Bucket: {MINIO_BUCKET}/{object_name}",
            )
        except Exception as e:
            bot.send_message(chat_id, f"Download failed: {e}")


@bot.message_handler(commands=["start"])
def settings(message):
    bot.send_message(message.chat.id, "Send a YouTube URL to download.")


@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text.strip()
    if not (
        text.startswith("https://www.youtube.com")
        or text.startswith("https://youtu.be")
    ):
        bot.send_message(message.chat.id, "Please send a valid YouTube URL.")
        return

    bot.send_message(message.chat.id, "Fetching formats...")
    title, formats = list_formats(text)
    if not formats:
        bot.send_message(message.chat.id, "No mp4 formats available.")
        return

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for f in formats[:20]:
        size = f" ({f['filesize'] / 1024 / 1024:.1f}MB)" if f.get("filesize") else ""
        label = f"{f['resolution'] or f['note'] or f['format_id']}{size}"
        cb_data = f"dl|{text}|{f['format_id']}"
        keyboard.add(types.InlineKeyboardButton(text=label, callback_data=cb_data))

    bot.send_message(
        message.chat.id,
        f"**{title}**\nSelect format:",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("dl|"))
def callback_format(call):
    _, url, format_id = call.data.split("|", 2)
    bot.edit_message_reply_markup(
        call.message.chat.id, call.message.message_id, reply_markup=None
    )
    bot.send_message(call.message.chat.id, f"Downloading {format_id}...")
    download_and_upload(url, format_id, call.message.chat.id)


if __name__ == "__main__":
    ensure_bucket()
    bot.infinity_polling(timeout=30000)

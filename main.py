import argparse
import sys
from yt_dlp import YoutubeDL


def download_video(url, output_path=".", quality="best", audio_only=False):
    ydl_opts = {
        'outtmpl': f'{output_path}/%(title)s.%(ext)s',
        'quiet': False,
        'no_warnings': False,
    }

    if audio_only:
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    else:
        ydl_opts['format'] = quality

    with YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            print(f"\nDownloaded: {info.get('title', 'Unknown')}")
            return True
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return False


def list_formats(url):
    ydl_opts = {'quiet': True}
    with YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [info])
            print(f"\nTitle: {info.get('title', 'Unknown')}")
            for f in formats:
                f_id = f.get('format_id', '?')
                ext = f.get('ext', '?')
                resolution = f.get('resolution', '?')
                note = f.get('format_note', '')
                filesize = f.get('filesize')
                size_str = f" ({filesize / 1024 / 1024:.1f}MB)" if filesize else ""
                print(f"{f_id}: {ext} - {resolution} {note}{size_str}")
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Download YouTube videos")
    parser.add_argument("url", help="URL of the video")
    parser.add_argument("-o", "--output", default=".",
                        help="Output directory (default: current dir)")
    parser.add_argument("-q", "--quality", default="best",
                        help="Video quality (e.g., best, 720p, 1080p)")
    parser.add_argument("-a", "--audio-only", action="store_true",
                        help="Download only audio as MP3")
    parser.add_argument("-l", "--list-formats", action="store_true",
                        help="List available formats and exit")

    args = parser.parse_args()

    if args.list_formats:
        list_formats(args.url)
    else:
        download_video(args.url, args.output, args.quality, args.audio_only)


if __name__ == "__main__":
    main()

import asyncio
import json
import subprocess
from pathlib import Path
from backend.config import settings


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True)


async def search_youtube(title: str, artist: str, limit: int = 3) -> list[dict]:
    query = f"{title} {artist} official"
    loop = asyncio.get_event_loop()
    proc = await loop.run_in_executor(
        None, _run,
        ["yt-dlp", f"ytsearch{limit}:{query}", "--dump-json", "--no-playlist", "--quiet"],
    )
    results = []
    for line in proc.stdout.decode().splitlines():
        try:
            data = json.loads(line.strip())
            results.append({
                "id": data.get("id"), "title": data.get("title"),
                "uploader": data.get("uploader"), "duration": data.get("duration"),
                "url": f"https://www.youtube.com/watch?v={data.get('id')}",
                "thumbnail": data.get("thumbnail"),
            })
        except (json.JSONDecodeError, AttributeError):
            continue
    return results


async def download_audio(youtube_url: str, output_path: str) -> str:
    Path(settings.temp_dir).mkdir(parents=True, exist_ok=True)
    out_template = output_path.replace(".mp3", "")
    loop = asyncio.get_event_loop()
    proc = await loop.run_in_executor(
        None, _run,
        ["yt-dlp", "--extract-audio", "--audio-format", "mp3",
         "--audio-quality", settings.default_mp3_bitrate,
         "--output", f"{out_template}.%(ext)s",
         "--no-playlist", "--quiet", "--no-warnings", youtube_url],
    )
    if proc.returncode != 0:
        raise RuntimeError(f"yt-dlp failed: {proc.stderr.decode()}")
    for ext in ["mp3", "m4a", "webm", "opus"]:
        candidate = f"{out_template}.{ext}"
        if Path(candidate).exists():
            return candidate
    raise FileNotFoundError(f"Downloaded file not found at {out_template}.*")

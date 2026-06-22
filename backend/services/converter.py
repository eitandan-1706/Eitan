import asyncio


async def convert_to_mp3(input_path: str, output_path: str, bitrate: str = "320k") -> str:
    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-y", "-i", input_path, "-vn", "-ar", "44100", "-ac", "2", "-b:a", bitrate, output_path,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg conversion failed: {stderr.decode()}")
    return output_path

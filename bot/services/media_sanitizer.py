import asyncio
import os
import tempfile
from typing import Optional


async def sanitize_media_file(input_path: str, media_type: str) -> Optional[str]:
    """Re-encode media to drop embedded metadata and return output path."""
    suffix = ".mp4" if media_type == "video" else ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as output_file:
        output_path = output_file.name

    if media_type == "video":
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            input_path,
            "-map_metadata",
            "-1",
            "-map_chapters",
            "-1",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "23",
            "-c:a",
            "aac",
            "-movflags",
            "+faststart",
            output_path,
        ]
    else:
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            input_path,
            "-map_metadata",
            "-1",
            output_path,
        ]

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, stderr = await process.communicate()

        if process.returncode != 0:
            print(f"ffmpeg sanitization failed: {stderr.decode(errors='ignore')}")
            if os.path.exists(output_path):
                os.remove(output_path)
            return None

        return output_path
    except Exception as e:
        print(f"Error sanitizing media: {e}")
        if os.path.exists(output_path):
            os.remove(output_path)
        return None

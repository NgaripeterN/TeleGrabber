import yt_dlp
import asyncio
import os
import shutil
import tempfile

# Define potential paths for the cookie file
COOKIE_PATH_LOCAL = "cookies.txt"
COOKIE_PATH_RENDER = "/etc/secrets/cookies.txt"

async def download_media(url: str):
    loop = asyncio.get_event_loop()
    ydl_opts = {
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'max_filesize': 50 * 1024 * 1024,  # 50MB
        'age_limit': 21,
        'ignoreerrors': True,
    }

    cookie_path_to_use = None
    temp_cookie_path = None

    if os.path.exists(COOKIE_PATH_LOCAL):
        cookie_path_to_use = COOKIE_PATH_LOCAL
    elif os.path.exists(COOKIE_PATH_RENDER):
        # Copy to a temporary, writable location
        temp_dir = tempfile.gettempdir()
        temp_cookie_path = os.path.join(temp_dir, 'cookies.txt')
        shutil.copy2(COOKIE_PATH_RENDER, temp_cookie_path)
        cookie_path_to_use = temp_cookie_path

    if cookie_path_to_use:
        ydl_opts['cookiefile'] = cookie_path_to_use

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True))
            
            filenames = []
            if 'entries' in info:
                # It's a playlist (multiple media)
                for entry in info.get('entries', []):
                    # For some reason, ydl.prepare_filename(entry) may not work if the entry is not a dict
                    if isinstance(entry, dict):
                        filenames.append(ydl.prepare_filename(entry))
            else:
                # It's a single media item
                filenames.append(ydl.prepare_filename(info))
            
            return filenames

    except Exception as e:
        print(f"Error downloading media: {e}")
        return []
    finally:
        # Clean up the temporary cookie file if it was created
        if temp_cookie_path and os.path.exists(temp_cookie_path):
            os.remove(temp_cookie_path)

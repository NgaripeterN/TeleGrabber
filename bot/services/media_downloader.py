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
        'format': 'bestvideo+bestaudio/best',
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

            if not info:
                return []
            
            filenames = []
            if 'entries' in info:
                for entry in info.get('entries', []):
                    if isinstance(entry, dict) and entry.get('filepath'):
                        filenames.append(entry['filepath'])
                    # Sometimes entries are not dicts, but have been processed
                    elif entry and not isinstance(entry, dict):
                         # This case is tricky, we assume ydl has a way to get the filename
                         # For now, we'll try to get it from the info dict if possible.
                         # This path is less certain.
                         prepared_fn = ydl.prepare_filename(info)
                         if prepared_fn and prepared_fn not in filenames:
                             filenames.append(prepared_fn)
            else:
                if info.get('filepath'):
                    filenames.append(info['filepath'])

            # Fallback if the above logic fails to find a path
            if not filenames and info.get('requested_downloads'):
                 for rd in info.get('requested_downloads', []):
                     if rd.get('filepath') and rd['filepath'] not in filenames:
                         filenames.append(rd['filepath'])

            return filenames

    except Exception as e:
        print(f"Error downloading media: {e}")
        return []
    finally:
        if temp_cookie_path and os.path.exists(temp_cookie_path):
            os.remove(temp_cookie_path)

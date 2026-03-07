import yt_dlp
import asyncio
import os

# Define potential paths for the cookie file
COOKIE_PATH_LOCAL = "cookies.txt"
COOKIE_PATH_RENDER = "/etc/secrets/cookies.txt"

async def download_media(url: str):
    loop = asyncio.get_event_loop()
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'noplaylist': True,
        'max_filesize': 50 * 1024 * 1024,  # 50MB
        'age_limit': 21,
    }

    # --- DEBUGGING ---
    print(f"DEBUG: Checking for cookies file...")
    if os.path.exists(COOKIE_PATH_LOCAL):
        print(f"DEBUG: cookies.txt FOUND at local path: {COOKIE_PATH_LOCAL}")
        ydl_opts['cookiefile'] = COOKIE_PATH_LOCAL
    elif os.path.exists(COOKIE_PATH_RENDER):
        print(f"DEBUG: cookies.txt FOUND at Render secret path: {COOKIE_PATH_RENDER}")
        ydl_opts['cookiefile'] = COOKIE_PATH_RENDER
    else:
        print("DEBUG: cookies.txt NOT FOUND in any known path.")
    
    print(f"DEBUG: Final yt-dlp options: {ydl_opts}")
    # --- END DEBUGGING ---

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True))
            return ydl.prepare_filename(info)
        except Exception as e:
            print(f"Error downloading media: {e}")
            return None

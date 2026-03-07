import yt_dlp
import asyncio
import os

COOKIES_FILE = "cookies.txt"

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
    print(f"DEBUG: Checking for cookies file at path: {os.path.abspath(COOKIES_FILE)}")
    if os.path.exists(COOKIES_FILE):
        print("DEBUG: cookies.txt FOUND. Adding to yt-dlp options.")
        ydl_opts['cookiefile'] = COOKIES_FILE
    else:
        print("DEBUG: cookies.txt NOT FOUND. Proceeding without authenticated session.")
    print(f"DEBUG: Final yt-dlp options: {ydl_opts}")
    # --- END DEBUGGING ---

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True))
            return ydl.prepare_filename(info)
        except Exception as e:
            print(f"Error downloading media: {e}")
            return None

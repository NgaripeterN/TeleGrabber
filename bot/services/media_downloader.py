import yt_dlp
import asyncio
import os
import shutil
import tempfile
import httpx

# Define potential paths for the cookie file
COOKIE_PATH_LOCAL = "cookies.txt"
COOKIE_PATH_RENDER = "/etc/secrets/cookies.txt"

async def download_media(url: str):
    loop = asyncio.get_event_loop()
    ydl_opts = {
        'quiet': True,
        'ignoreerrors': True,
    }

    cookie_path_to_use = None
    temp_cookie_path = None
    downloaded_files = []

    if os.path.exists(COOKIE_PATH_LOCAL):
        cookie_path_to_use = COOKIE_PATH_LOCAL
    elif os.path.exists(COOKIE_PATH_RENDER):
        temp_dir = tempfile.gettempdir()
        temp_cookie_path = os.path.join(temp_dir, 'cookies.txt')
        shutil.copy2(COOKIE_PATH_RENDER, temp_cookie_path)
        cookie_path_to_use = temp_cookie_path

    if cookie_path_to_use:
        ydl_opts['cookiefile'] = cookie_path_to_use

    try:
        # Step 1: Use yt-dlp to extract metadata only
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))

        if not info:
            print("Error: yt-dlp failed to extract metadata.")
            return []

        # Step 2: Find all media URLs from the metadata
        media_urls = []
        if 'entries' in info: # Multiple media items
            for entry in info.get('entries', []):
                if isinstance(entry, dict) and entry.get('url'):
                    media_urls.append(entry['url'])
        elif 'url' in info: # Single media item
            media_urls.append(info['url'])
        
        if not media_urls:
            print("Error: Could not find any media URLs in the extracted metadata.")
            return []

        # Step 3: Download the URLs directly using httpx
        async with httpx.AsyncClient() as client:
            for i, media_url in enumerate(media_urls):
                try:
                    # Create a temporary file to save the download
                    # We give it a suffix based on the original URL to help with file type
                    file_suffix = os.path.splitext(media_url.split('?')[0])[-1] or '.tmp'
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=file_suffix)
                    
                    async with client.stream('GET', media_url, timeout=30.0) as response:
                        response.raise_for_status()
                        with open(temp_file.name, 'wb') as f:
                            async for chunk in response.aiter_bytes():
                                f.write(chunk)
                    
                    downloaded_files.append(temp_file.name)
                    print(f"Successfully downloaded {media_url} to {temp_file.name}")

                except Exception as e:
                    print(f"Failed to download individual URL {media_url}: {e}")
        
        return downloaded_files

    except Exception as e:
        print(f"A top-level error occurred in download_media: {e}")
        return []
    finally:
        # Clean up the temporary cookie file if it was created
        if temp_cookie_path and os.path.exists(temp_cookie_path):
            os.remove(temp_cookie_path)
        # Note: The caller is responsible for cleaning up the downloaded media files

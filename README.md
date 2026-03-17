# Telegram Media & Moderation Bot

A subscription-based Telegram bot built with FastAPI that helps manage groups.

## Features

- Deletes "user joined/left" messages.
- Basic anti-spam protection against message flooding.
- When an admin posts a link from Twitter/X or Reddit, the bot downloads the media (including audio), posts it directly to the group, and deletes the original message.
- Built-in subscription system using Telegram Stars.

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <https://github.com/NgaripeterN/TeleGrabber>
    cd <your-repo-name>
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Install FFmpeg (Required for audio/video merging):**
    - **On Debian/Ubuntu:** `sudo apt-get install ffmpeg`
    - **On macOS:** `brew install ffmpeg`
    - **On Windows:** Download from the [official site](https://ffmpeg.org/download.html) and add to your PATH.

## Configuration

1.  **Create a `.env` file** in the root of the project. This file will hold your secret keys.

2.  **Add the following variables** to your `.env` file:

    ```ini
    TELEGRAM_BOT_TOKEN="YOUR_BOT_TOKEN"
    OWNER_ID="YOUR_TELEGRAM_ID"
    DATABASE_URL="sqlite:///./bot.db"
    WEBHOOK_URL="https://your-service-name.onrender.com"
    ```
    - `TELEGRAM_BOT_TOKEN`: Get this from `@BotFather` on Telegram.
    - `OWNER_ID`: Your personal Telegram user ID. Used for owner-only commands.
    - `WEBHOOK_URL`: The public URL where your bot is hosted.

3.  **(Optional but Recommended) Create `cookies.txt`:**
    For the best results downloading media from sites that require a login (like Twitter and Reddit), create a `cookies.txt` file in the root directory. Make sure you are logged into both sites in your browser when you export the cookies.

## Running the Bot

### Locally
For local testing, you'll need a tool like `ngrok` to expose a public URL for your webhook. Update `WEBHOOK_URL` in your `.env` file with the ngrok URL.

Then, run the app with Uvicorn:
```bash
uvicorn bot.main:app --reload --port 8000
```

### Deployment on Render (Recommended)
This bot is set up for easy deployment on Render's free tier.

- **Build Command:** `pip install -r requirements.txt && apt-get update && apt-get install -y ffmpeg`
- **Start Command:** `uvicorn bot.main:app --host 0.0.0.0 --port 10000`

- **Environment Variables:** Add the variables from your `.env` file to the Render dashboard under **Environment**.
- **Database:** Use `sqlite:///var/data/bot.db` as the `DATABASE_URL` to persist your database.
- **Cookies:** If using `cookies.txt`, add it as a **Secret File** in the Render dashboard.

## Telegram Bot Setup

1.  **BotFather:**
    - Create your bot to get the token.
    - Go to `Bot Settings -> Payments` and connect the **Telegram Stars** provider.

2.  **Group Admin Privileges:**
    When you add the bot to a group, promote it to an admin and grant it the following rights:
    - `Delete Messages`
    - `Post Messages`

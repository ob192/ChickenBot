import os

from dotenv import load_dotenv

load_dotenv(".env.local")
load_dotenv()

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
DATABASE_URL = os.environ["DATABASE_URL"]

# Shared secret the admin UI (or any client) must send as X-API-Key.
# Read lazily by the API only, so the bot can run without it.
API_KEY = os.getenv("API_KEY", "")

# Comma-separated origins allowed to call the API from a browser.
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]

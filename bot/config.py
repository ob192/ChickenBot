import os

from dotenv import load_dotenv

load_dotenv(".env.local")
load_dotenv()

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
DATABASE_URL = os.environ["DATABASE_URL"]

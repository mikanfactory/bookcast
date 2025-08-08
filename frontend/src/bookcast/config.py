import os

from dotenv import load_dotenv

load_dotenv()

ENV = os.getenv("ENV", "development")

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

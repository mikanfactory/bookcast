import os

from dotenv import load_dotenv

load_dotenv()

ENV = os.getenv("ENV", "development")

if ENV == "production":
    GOOGLE_CLOUD_STORAGE_BUCKET = os.getenv("GOOGLE_CLOUD_PRODUCTION_STORAGE_BUCKET")
else:
    GOOGLE_CLOUD_STORAGE_BUCKET = os.getenv("GOOGLE_CLOUD_DEVELOPMENT_STORAGE_BUCKET")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

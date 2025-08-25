import os

from dotenv import load_dotenv

load_dotenv()

ENV = os.getenv("ENV", "development")

GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
if ENV == "production":
    GOOGLE_CLOUD_STORAGE_BUCKET = os.getenv("GOOGLE_CLOUD_PRODUCTION_STORAGE_BUCKET")
else:
    GOOGLE_CLOUD_STORAGE_BUCKET = os.getenv("GOOGLE_CLOUD_DEVELOPMENT_STORAGE_BUCKET")

BACKEND_URL = os.getenv("BACKEND_URL")

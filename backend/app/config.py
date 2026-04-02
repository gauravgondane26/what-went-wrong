import os
from dotenv import load_dotenv

load_dotenv()

STATSBOMB_BASE_URL = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"
# Optional: point to a local clone of statsbomb/open-data to bypass HTTP rate limits.
# e.g. STATSBOMB_LOCAL_PATH=/home/user/open-data/data
STATSBOMB_LOCAL_PATH: str | None = os.getenv("STATSBOMB_LOCAL_PATH")

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

HTTP_TIMEOUT_SECONDS = float(os.getenv("HTTP_TIMEOUT_SECONDS", "30"))
HTTP_MAX_RETRIES = int(os.getenv("HTTP_MAX_RETRIES", "3"))

CACHE_MAX_SIZE = int(os.getenv("CACHE_MAX_SIZE", "20"))
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "3600"))

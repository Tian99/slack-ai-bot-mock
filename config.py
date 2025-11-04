import os
from dotenv import load_dotenv

"""
App configuration loader — loads environment variables from .env or system.
Provides defaults for local development.
"""

load_dotenv()

SLACK_SIGNING_SECRET = os.getenv("SLACK_SIGNING_SECRET", "dev-secret")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DOCS_DIR = os.getenv("DOCS_DIR", "docs")

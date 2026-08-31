"""Configuration settings for the JSON2Video Streamlit micro-app."""

import os

JSON2VIDEO_BASE_URL = os.getenv("JSON2VIDEO_BASE_URL", "https://api.json2video.com")
DEFAULT_TIMEOUT = int(os.getenv("DEFAULT_TIMEOUT", "30"))
UPLOAD_TIMEOUT = int(os.getenv("UPLOAD_TIMEOUT", "90"))
POLL_INTERVAL_SECONDS = int(os.getenv("POLL_INTERVAL_SECONDS", "3"))
RENDER_WAIT_TIMEOUT = int(os.getenv("RENDER_WAIT_TIMEOUT", "300"))

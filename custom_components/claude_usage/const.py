"""Constants for the Claude Usage integration."""

from datetime import timedelta

DOMAIN = "claude_usage"

CONF_SESSION_KEY = "session_key"

API_BASE_URL = "https://claude.ai/api"
API_ORGANIZATIONS_URL = f"{API_BASE_URL}/organizations"

UPDATE_INTERVAL = timedelta(minutes=5)

PLATFORMS = ["sensor"]

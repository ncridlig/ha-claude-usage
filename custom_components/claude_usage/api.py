"""API client for Claude.ai usage data."""

from __future__ import annotations

import aiohttp

from .const import API_BASE_URL, API_ORGANIZATIONS_URL


class ClaudeApiError(Exception):
    """Base exception for Claude API errors."""


class ClaudeApiAuthError(ClaudeApiError):
    """Authentication error (401/403)."""


class ClaudeApiClient:
    """Async client for the Claude.ai usage API."""

    def __init__(self, session: aiohttp.ClientSession, session_key: str) -> None:
        """Initialize the API client."""
        self._session = session
        self._session_key = session_key
        self._org_id: str | None = None

    @property
    def _headers(self) -> dict[str, str]:
        """Return request headers with session cookie."""
        return {"Cookie": f"sessionKey={self._session_key}"}

    async def async_get_org_id(self) -> str:
        """Fetch and cache the organization ID."""
        if self._org_id is not None:
            return self._org_id

        try:
            async with self._session.get(
                API_ORGANIZATIONS_URL, headers=self._headers
            ) as resp:
                if resp.status in (401, 403):
                    raise ClaudeApiAuthError("Session key is invalid or expired")
                if resp.status != 200:
                    raise ClaudeApiError(f"Unexpected status {resp.status}")
                data = await resp.json()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise ClaudeApiError(f"Connection error: {err}") from err

        if not data or not isinstance(data, list):
            raise ClaudeApiError("Unexpected response format for organizations")

        self._org_id = data[0].get("uuid") or data[0].get("id")
        if not self._org_id:
            raise ClaudeApiError("Could not find organization ID in response")

        return self._org_id

    async def async_get_usage(self) -> dict:
        """Fetch current usage data."""
        org_id = await self.async_get_org_id()
        url = f"{API_BASE_URL}/organizations/{org_id}/usage"

        try:
            async with self._session.get(url, headers=self._headers) as resp:
                if resp.status in (401, 403):
                    self._org_id = None
                    raise ClaudeApiAuthError("Session key is invalid or expired")
                if resp.status != 200:
                    raise ClaudeApiError(f"Unexpected status {resp.status}")
                return await resp.json()
        except (aiohttp.ClientError, TimeoutError) as err:
            raise ClaudeApiError(f"Connection error: {err}") from err

    async def async_validate_session_key(self) -> str:
        """Validate the session key by fetching the org ID. Returns org ID."""
        self._org_id = None
        return await self.async_get_org_id()

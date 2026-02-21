"""API client for Claude.ai usage data."""

from __future__ import annotations

import uuid

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
        """Return request headers with session cookie and browser User-Agent."""
        return {
            "Cookie": f"sessionKey={self._session_key}",
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
        }

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

    async def async_send_renewal_message(self) -> None:
        """Send a minimal message to claude.ai to restart the weekly usage cycle.

        Creates a temporary conversation, sends "hi", then deletes it.
        """
        org_id = await self.async_get_org_id()
        conv_uuid = str(uuid.uuid4())
        base = f"{API_BASE_URL}/organizations/{org_id}/chat_conversations"

        try:
            # Create a temporary conversation
            async with self._session.post(
                base,
                headers={**self._headers, "Content-Type": "application/json"},
                json={"uuid": conv_uuid, "name": ""},
            ) as resp:
                if resp.status in (401, 403):
                    raise ClaudeApiAuthError("Session key is invalid or expired")
                if resp.status != 201:
                    raise ClaudeApiError(
                        f"Failed to create conversation: status {resp.status}"
                    )

            # Send a minimal message (SSE stream — read a chunk to confirm success)
            async with self._session.post(
                f"{base}/{conv_uuid}/completion",
                headers={
                    **self._headers,
                    "Content-Type": "application/json",
                    "Accept": "text/event-stream",
                },
                json={
                    "prompt": "hi",
                    "timezone": "UTC",
                    "attachments": [],
                    "files": [],
                },
            ) as resp:
                if resp.status in (401, 403):
                    raise ClaudeApiAuthError("Session key is invalid or expired")
                if resp.status != 200:
                    raise ClaudeApiError(
                        f"Failed to send message: status {resp.status}"
                    )
                # Read a small chunk to ensure the request is accepted
                await resp.content.read(256)

        except (aiohttp.ClientError, TimeoutError) as err:
            raise ClaudeApiError(f"Connection error: {err}") from err
        finally:
            # Always try to delete the temporary conversation
            try:
                await self._session.delete(
                    f"{base}/{conv_uuid}", headers=self._headers
                )
            except Exception:  # noqa: BLE001
                pass

    async def async_validate_session_key(self) -> str:
        """Validate the session key by fetching the org ID. Returns org ID."""
        self._org_id = None
        return await self.async_get_org_id()

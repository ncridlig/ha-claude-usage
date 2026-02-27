"""DataUpdateCoordinator for Claude Usage."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ClaudeApiAuthError, ClaudeApiClient, ClaudeApiError
from .const import CONF_AUTO_RENEW, CONF_AUTO_RENEW_SESSION, DOMAIN, UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class ClaudeUsageCoordinator(DataUpdateCoordinator[dict]):
    """Coordinator that polls Claude.ai usage data every 5 minutes."""

    def __init__(
        self, hass: HomeAssistant, client: ClaudeApiClient, entry: ConfigEntry
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
            config_entry=entry,
        )
        self.client = client

    async def _async_update_data(self) -> dict:
        """Fetch usage data from the API."""
        try:
            data = await self.client.async_get_usage()
        except ClaudeApiAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except ClaudeApiError as err:
            raise UpdateFailed(str(err)) from err

        # Auto-renew: if either cycle has expired and its switch is enabled,
        # send a single minimal message to restart both windows.
        session_expired = data.get("five_hour", {}).get("resets_at") is None
        weekly_expired = data.get("seven_day", {}).get("resets_at") is None
        session_renew = self.config_entry.options.get(CONF_AUTO_RENEW_SESSION, False)
        weekly_renew = self.config_entry.options.get(CONF_AUTO_RENEW, False)

        should_renew = (session_expired and session_renew) or (
            weekly_expired and weekly_renew
        )

        if should_renew:
            _LOGGER.info("Usage cycle expired, auto-renewing with a renewal message")
            try:
                await self.client.async_send_renewal_message()
                # Re-fetch usage to get the updated reset timestamps
                data = await self.client.async_get_usage()
            except ClaudeApiAuthError as err:
                raise ConfigEntryAuthFailed(str(err)) from err
            except ClaudeApiError as err:
                _LOGGER.warning("Auto-renewal failed: %s", err)

        return data

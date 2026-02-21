"""DataUpdateCoordinator for Claude Usage."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ClaudeApiAuthError, ClaudeApiClient, ClaudeApiError
from .const import CONF_AUTO_RENEW, DOMAIN, UPDATE_INTERVAL

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

        # Auto-renew: if the weekly cycle has expired and auto_renew is enabled,
        # send a minimal message to restart the 7-day window.
        weekly_reset = data.get("seven_day", {}).get("resets_at")
        auto_renew = self.config_entry.options.get(CONF_AUTO_RENEW, False)

        if weekly_reset is None and auto_renew:
            _LOGGER.info("Weekly cycle expired, auto-renewing with a renewal message")
            try:
                await self.client.async_send_renewal_message()
                # Re-fetch usage to get the updated reset timestamp
                data = await self.client.async_get_usage()
            except ClaudeApiAuthError as err:
                raise ConfigEntryAuthFailed(str(err)) from err
            except ClaudeApiError as err:
                _LOGGER.warning("Auto-renewal failed: %s", err)

        return data

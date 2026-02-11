"""DataUpdateCoordinator for Claude Usage."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ClaudeApiAuthError, ClaudeApiClient, ClaudeApiError
from .const import DOMAIN, UPDATE_INTERVAL

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
            return await self.client.async_get_usage()
        except ClaudeApiAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except ClaudeApiError as err:
            raise UpdateFailed(str(err)) from err

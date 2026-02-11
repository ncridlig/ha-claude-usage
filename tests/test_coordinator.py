"""Tests for the Claude Usage coordinator."""

from unittest.mock import AsyncMock

import pytest

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.claude_usage.api import (
    ClaudeApiAuthError,
    ClaudeApiClient,
    ClaudeApiError,
)
from custom_components.claude_usage.const import DOMAIN
from custom_components.claude_usage.coordinator import ClaudeUsageCoordinator

from .conftest import MOCK_USAGE_RESPONSE


async def test_successful_update(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Test coordinator returns data on success."""
    mock_config_entry.add_to_hass(hass)
    client = AsyncMock(spec=ClaudeApiClient)
    client.async_get_usage.return_value = MOCK_USAGE_RESPONSE

    coordinator = ClaudeUsageCoordinator(hass, client, mock_config_entry)
    await coordinator.async_refresh()

    assert coordinator.last_update_success is True
    assert coordinator.data == MOCK_USAGE_RESPONSE
    assert coordinator.data["five_hour"]["utilization"] == 45.0


async def test_auth_error_on_first_refresh(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Test auth errors raise ConfigEntryAuthFailed on first refresh."""
    mock_config_entry.add_to_hass(hass)
    mock_config_entry.mock_state(hass, ConfigEntryState.SETUP_IN_PROGRESS)
    client = AsyncMock(spec=ClaudeApiClient)
    client.async_get_usage.side_effect = ClaudeApiAuthError("expired")

    coordinator = ClaudeUsageCoordinator(hass, client, mock_config_entry)

    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator.async_config_entry_first_refresh()


async def test_api_error_raises_update_failed(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Test generic API errors are mapped to UpdateFailed."""
    mock_config_entry.add_to_hass(hass)
    client = AsyncMock(spec=ClaudeApiClient)
    client.async_get_usage.side_effect = ClaudeApiError("timeout")

    coordinator = ClaudeUsageCoordinator(hass, client, mock_config_entry)
    await coordinator.async_refresh()

    assert coordinator.last_update_success is False

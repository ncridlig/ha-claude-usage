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
from custom_components.claude_usage.const import CONF_AUTO_RENEW, DOMAIN
from custom_components.claude_usage.coordinator import ClaudeUsageCoordinator

from .conftest import MOCK_USAGE_RESPONSE

MOCK_EXPIRED_USAGE = {
    "five_hour": {"utilization": 0.0, "resets_at": None},
    "seven_day": {"utilization": 0.0, "resets_at": None},
}

MOCK_RENEWED_USAGE = {
    "five_hour": {"utilization": 1.0, "resets_at": "2026-02-21T15:00:00+00:00"},
    "seven_day": {"utilization": 1.0, "resets_at": "2026-02-28T00:00:00+00:00"},
}


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


async def test_auto_renew_sends_message_when_expired(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Test auto-renewal sends a message when weekly cycle has expired."""
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry, options={CONF_AUTO_RENEW: True}
    )

    client = AsyncMock(spec=ClaudeApiClient)
    # First call returns expired, second call (after renewal) returns renewed
    client.async_get_usage.side_effect = [MOCK_EXPIRED_USAGE, MOCK_RENEWED_USAGE]

    coordinator = ClaudeUsageCoordinator(hass, client, mock_config_entry)
    await coordinator.async_refresh()

    assert coordinator.last_update_success is True
    client.async_send_renewal_message.assert_called_once()
    # Data should be the renewed response (second call)
    assert coordinator.data == MOCK_RENEWED_USAGE


async def test_no_auto_renew_when_disabled(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Test no renewal message is sent when auto_renew is off."""
    mock_config_entry.add_to_hass(hass)
    # auto_renew defaults to False (not set in options)

    client = AsyncMock(spec=ClaudeApiClient)
    client.async_get_usage.return_value = MOCK_EXPIRED_USAGE

    coordinator = ClaudeUsageCoordinator(hass, client, mock_config_entry)
    await coordinator.async_refresh()

    assert coordinator.last_update_success is True
    client.async_send_renewal_message.assert_not_called()
    assert coordinator.data == MOCK_EXPIRED_USAGE


async def test_no_auto_renew_when_not_expired(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Test no renewal when weekly cycle is still active."""
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry, options={CONF_AUTO_RENEW: True}
    )

    client = AsyncMock(spec=ClaudeApiClient)
    client.async_get_usage.return_value = MOCK_USAGE_RESPONSE  # has resets_at set

    coordinator = ClaudeUsageCoordinator(hass, client, mock_config_entry)
    await coordinator.async_refresh()

    assert coordinator.last_update_success is True
    client.async_send_renewal_message.assert_not_called()


async def test_auto_renew_failure_still_returns_data(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Test that renewal failure doesn't break the update — original data is returned."""
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry, options={CONF_AUTO_RENEW: True}
    )

    client = AsyncMock(spec=ClaudeApiClient)
    client.async_get_usage.return_value = MOCK_EXPIRED_USAGE
    client.async_send_renewal_message.side_effect = ClaudeApiError("network error")

    coordinator = ClaudeUsageCoordinator(hass, client, mock_config_entry)
    await coordinator.async_refresh()

    assert coordinator.last_update_success is True
    assert coordinator.data == MOCK_EXPIRED_USAGE


async def test_auto_renew_auth_failure_triggers_reauth(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Test that auth failure during renewal triggers reauth."""
    mock_config_entry.add_to_hass(hass)
    mock_config_entry.mock_state(hass, ConfigEntryState.SETUP_IN_PROGRESS)
    hass.config_entries.async_update_entry(
        mock_config_entry, options={CONF_AUTO_RENEW: True}
    )

    client = AsyncMock(spec=ClaudeApiClient)
    client.async_get_usage.return_value = MOCK_EXPIRED_USAGE
    client.async_send_renewal_message.side_effect = ClaudeApiAuthError("expired key")

    coordinator = ClaudeUsageCoordinator(hass, client, mock_config_entry)

    with pytest.raises(ConfigEntryAuthFailed):
        await coordinator.async_config_entry_first_refresh()

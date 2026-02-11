"""Tests for Claude Usage integration setup and teardown."""

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.claude_usage.const import DOMAIN


async def test_setup_entry(
    hass: HomeAssistant, setup_integration: MockConfigEntry
) -> None:
    """Test successful setup creates coordinator and loads sensors."""
    entry = setup_integration
    assert entry.state is ConfigEntryState.LOADED
    assert DOMAIN in hass.data
    assert entry.entry_id in hass.data[DOMAIN]


async def test_unload_entry(
    hass: HomeAssistant, setup_integration: MockConfigEntry
) -> None:
    """Test unload removes data and transitions to NOT_LOADED."""
    entry = setup_integration
    assert entry.state is ConfigEntryState.LOADED

    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.NOT_LOADED
    assert entry.entry_id not in hass.data.get(DOMAIN, {})


async def test_setup_auth_failure(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test setup fails gracefully on auth error, triggers reauth."""
    aioclient_mock.get("https://claude.ai/api/organizations", status=401)

    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR

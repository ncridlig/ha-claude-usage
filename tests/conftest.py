"""Shared fixtures for Claude Usage tests."""

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker
from homeassistant.core import HomeAssistant
from homeassistant.loader import DATA_CUSTOM_COMPONENTS

from custom_components.claude_usage.const import DOMAIN


@pytest.fixture(autouse=True)
def enable_custom_integrations(hass: HomeAssistant) -> None:
    """Enable loading of custom integrations in the test hass instance."""
    hass.data.pop(DATA_CUSTOM_COMPONENTS, None)

ORG_URL = "https://claude.ai/api/organizations"
USAGE_URL = "https://claude.ai/api/organizations/org-test-uuid/usage"

MOCK_ORG_RESPONSE = [{"uuid": "org-test-uuid"}]

MOCK_USAGE_RESPONSE = {
    "five_hour": {"utilization": 45.0, "resets_at": "2026-02-10T15:30:00+00:00"},
    "seven_day": {"utilization": 72.0, "resets_at": "2026-02-17T00:00:00+00:00"},
}


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={"session_key": "sk-ant-test-key"},
        unique_id="org-test-uuid",
        title="Claude Usage",
        version=1,
    )


@pytest.fixture
def mock_api(aioclient_mock: AiohttpClientMocker) -> AiohttpClientMocker:
    """Mock both API endpoints with default successful responses."""
    aioclient_mock.get(ORG_URL, json=MOCK_ORG_RESPONSE)
    aioclient_mock.get(USAGE_URL, json=MOCK_USAGE_RESPONSE)
    return aioclient_mock


@pytest.fixture
async def setup_integration(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_api: AiohttpClientMocker,
) -> MockConfigEntry:
    """Set up the integration with mocked API."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    return mock_config_entry

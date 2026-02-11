"""Tests for the Claude Usage config flow."""

import aiohttp

from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.test_util.aiohttp import AiohttpClientMocker

from custom_components.claude_usage.const import DOMAIN

from .conftest import ORG_URL


async def test_full_user_flow(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test the happy path: user enters valid key, entry is created."""
    aioclient_mock.get(ORG_URL, json=[{"uuid": "org-123"}])

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"session_key": "sk-valid"},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Claude Usage"
    assert result["data"] == {"session_key": "sk-valid"}

    entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert entry.unique_id == "org-123"


async def test_invalid_auth(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test form shows error on 401."""
    aioclient_mock.get(ORG_URL, status=401)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"session_key": "sk-bad"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_cannot_connect(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test form shows error on connection failure."""
    aioclient_mock.get(ORG_URL, exc=aiohttp.ClientError())

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"session_key": "sk-test"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_duplicate_entry(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that a duplicate org ID is rejected."""
    mock_config_entry.add_to_hass(hass)
    aioclient_mock.get(ORG_URL, json=[{"uuid": "org-test-uuid"}])

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"session_key": "sk-another"},
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_reauth_flow(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test reauthentication updates the stored key and reloads."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    aioclient_mock.get(ORG_URL, json=[{"uuid": "org-test-uuid"}])

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"session_key": "sk-new-key"},
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert mock_config_entry.data["session_key"] == "sk-new-key"


async def test_reauth_invalid_auth(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test reauth shows error on bad key."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reauth_flow(hass)
    aioclient_mock.get(ORG_URL, status=403)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"session_key": "sk-still-bad"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}

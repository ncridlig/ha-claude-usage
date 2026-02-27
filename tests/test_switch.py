"""Tests for the Claude Usage auto-renew switch."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.claude_usage.const import (
    CONF_AUTO_RENEW,
    CONF_AUTO_RENEW_SESSION,
    DOMAIN,
)


def _get_switch_entity_id(
    entity_registry: er.EntityRegistry, entry_id: str, key: str = "auto_renew"
) -> str:
    """Look up a switch entity_id by unique_id suffix."""
    for entity in er.async_entries_for_config_entry(entity_registry, entry_id):
        if entity.unique_id.endswith(f"_{key}"):
            return entity.entity_id
    raise AssertionError(f"No {key} switch entity found")


async def test_switch_created(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test the auto-renew switch is created and defaults to off."""
    eid = setup_integration.entry_id
    entity_id = _get_switch_entity_id(entity_registry, eid)
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "off"


async def test_switch_turn_on(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test turning on the auto-renew switch."""
    eid = setup_integration.entry_id
    entity_id = _get_switch_entity_id(entity_registry, eid)

    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": entity_id}, blocking=True
    )
    await hass.async_block_till_done()

    assert setup_integration.options.get(CONF_AUTO_RENEW) is True
    state = hass.states.get(entity_id)
    assert state.state == "on"


async def test_switch_turn_off(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test turning off the auto-renew switch."""
    eid = setup_integration.entry_id
    entity_id = _get_switch_entity_id(entity_registry, eid)

    # Turn on first
    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": entity_id}, blocking=True
    )
    await hass.async_block_till_done()
    assert setup_integration.options.get(CONF_AUTO_RENEW) is True

    # Turn off
    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": entity_id}, blocking=True
    )
    await hass.async_block_till_done()

    assert setup_integration.options.get(CONF_AUTO_RENEW) is False
    state = hass.states.get(entity_id)
    assert state.state == "off"


async def test_switch_shares_device(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test both switches are under the same device as sensors."""
    devices = dr.async_entries_for_config_entry(
        device_registry, setup_integration.entry_id
    )
    # All entities (sensors + switches) should share a single device
    assert len(devices) == 1
    assert devices[0].name == "Claude Usage"


# --- Session auto-renew switch tests ---


async def test_session_switch_created(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test the session auto-renew switch is created and defaults to off."""
    eid = setup_integration.entry_id
    entity_id = _get_switch_entity_id(entity_registry, eid, "auto_renew_session")
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "off"


async def test_session_switch_turn_on(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test turning on the session auto-renew switch."""
    eid = setup_integration.entry_id
    entity_id = _get_switch_entity_id(entity_registry, eid, "auto_renew_session")

    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": entity_id}, blocking=True
    )
    await hass.async_block_till_done()

    assert setup_integration.options.get(CONF_AUTO_RENEW_SESSION) is True
    state = hass.states.get(entity_id)
    assert state.state == "on"


async def test_session_switch_turn_off(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test turning off the session auto-renew switch."""
    eid = setup_integration.entry_id
    entity_id = _get_switch_entity_id(entity_registry, eid, "auto_renew_session")

    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": entity_id}, blocking=True
    )
    await hass.async_block_till_done()
    assert setup_integration.options.get(CONF_AUTO_RENEW_SESSION) is True

    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": entity_id}, blocking=True
    )
    await hass.async_block_till_done()

    assert setup_integration.options.get(CONF_AUTO_RENEW_SESSION) is False
    state = hass.states.get(entity_id)
    assert state.state == "off"

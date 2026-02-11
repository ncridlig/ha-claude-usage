"""Tests for Claude Usage sensor entities."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.claude_usage.const import DOMAIN


def _get_entity_id_by_key(
    entity_registry: er.EntityRegistry, entry_id: str, key: str
) -> str:
    """Look up entity_id by the sensor key suffix in the unique_id."""
    for entity in er.async_entries_for_config_entry(entity_registry, entry_id):
        if entity.unique_id.endswith(f"_{key}"):
            return entity.entity_id
    raise AssertionError(f"No entity found with key '{key}'")


async def test_sensors_created(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test all 4 sensors are created with correct values."""
    eid = setup_integration.entry_id

    session_usage_id = _get_entity_id_by_key(entity_registry, eid, "session_usage")
    state = hass.states.get(session_usage_id)
    assert state is not None
    assert state.state == "45.0"

    weekly_usage_id = _get_entity_id_by_key(entity_registry, eid, "weekly_usage")
    state = hass.states.get(weekly_usage_id)
    assert state is not None
    assert state.state == "72.0"

    session_reset_id = _get_entity_id_by_key(entity_registry, eid, "session_reset")
    state = hass.states.get(session_reset_id)
    assert state is not None
    assert state.state == "2026-02-10T15:30:00+00:00"

    weekly_reset_id = _get_entity_id_by_key(entity_registry, eid, "weekly_reset")
    state = hass.states.get(weekly_reset_id)
    assert state is not None
    assert state.state == "2026-02-17T00:00:00+00:00"


async def test_device_created(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test a single device is registered with correct info."""
    devices = dr.async_entries_for_config_entry(
        device_registry, setup_integration.entry_id
    )
    assert len(devices) == 1

    device = devices[0]
    assert device.name == "Claude Usage"
    assert device.manufacturer == "Anthropic"
    assert device.entry_type is dr.DeviceEntryType.SERVICE


async def test_entities_registered(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test all 4 entities are registered under the integration."""
    entries = er.async_entries_for_config_entry(
        entity_registry, setup_integration.entry_id
    )
    assert len(entries) == 4

    keys = {e.unique_id.split("_", 1)[1] for e in entries}
    assert keys == {"session_usage", "weekly_usage", "session_reset", "weekly_reset"}

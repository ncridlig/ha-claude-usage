"""Sensor platform for Claude Usage."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util.dt import parse_datetime

from .const import DOMAIN
from .coordinator import ClaudeUsageCoordinator


@dataclass(frozen=True, kw_only=True)
class ClaudeUsageSensorEntityDescription(SensorEntityDescription):
    """Describe a Claude Usage sensor entity."""

    value_fn: Callable[[dict], float | datetime | None]


def _parse_reset_time(data: dict, period: str) -> datetime | None:
    """Parse a reset timestamp from the API response."""
    raw = data.get(period, {}).get("resets_at")
    if raw is None:
        return None
    return parse_datetime(raw)


SENSOR_DESCRIPTIONS: tuple[ClaudeUsageSensorEntityDescription, ...] = (
    ClaudeUsageSensorEntityDescription(
        key="session_usage",
        name="Current session",
        icon="mdi:timer-sand",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda data: data.get("five_hour", {}).get("utilization"),
    ),
    ClaudeUsageSensorEntityDescription(
        key="weekly_usage",
        name="Weekly limit",
        icon="mdi:calendar-week",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda data: data.get("seven_day", {}).get("utilization"),
    ),
    ClaudeUsageSensorEntityDescription(
        key="session_reset",
        name="Current session reset",
        icon="mdi:timer-refresh-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: _parse_reset_time(data, "five_hour"),
    ),
    ClaudeUsageSensorEntityDescription(
        key="weekly_reset",
        name="Weekly limit reset",
        icon="mdi:calendar-refresh-outline",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: _parse_reset_time(data, "seven_day"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Claude Usage sensor entities."""
    coordinator: ClaudeUsageCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        ClaudeUsageSensor(coordinator, description, entry)
        for description in SENSOR_DESCRIPTIONS
    )


class ClaudeUsageSensor(CoordinatorEntity[ClaudeUsageCoordinator], SensorEntity):
    """Sensor entity for Claude usage data."""

    entity_description: ClaudeUsageSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ClaudeUsageCoordinator,
        description: ClaudeUsageSensorEntityDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Claude Usage",
            manufacturer="Anthropic",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def native_value(self) -> float | datetime | None:
        """Return the sensor value."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

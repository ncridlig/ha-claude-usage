"""Switch platform for Claude Usage auto-renewal."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_AUTO_RENEW, CONF_AUTO_RENEW_SESSION, DOMAIN
from .coordinator import ClaudeUsageCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the auto-renew switch."""
    coordinator: ClaudeUsageCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        AutoRenewSwitch(coordinator, entry),
        AutoRenewSessionSwitch(coordinator, entry),
    ])


class AutoRenewSwitch(SwitchEntity):
    """Switch to enable automatic weekly cycle renewal."""

    _attr_has_entity_name = True
    _attr_name = "Automatic renew"
    _attr_icon = "mdi:autorenew"

    def __init__(
        self,
        coordinator: ClaudeUsageCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the switch."""
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_auto_renew"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Claude Usage",
            manufacturer="Anthropic",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def is_on(self) -> bool:
        """Return true if auto-renew is enabled."""
        return self._entry.options.get(CONF_AUTO_RENEW, False)

    async def async_turn_on(self, **kwargs) -> None:
        """Enable auto-renew."""
        self.hass.config_entries.async_update_entry(
            self._entry,
            options={**self._entry.options, CONF_AUTO_RENEW: True},
        )
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Disable auto-renew."""
        self.hass.config_entries.async_update_entry(
            self._entry,
            options={**self._entry.options, CONF_AUTO_RENEW: False},
        )
        self.async_write_ha_state()


class AutoRenewSessionSwitch(SwitchEntity):
    """Switch to enable automatic session (5-hour) cycle renewal."""

    _attr_has_entity_name = True
    _attr_name = "Automatic renew session"
    _attr_icon = "mdi:autorenew"

    def __init__(
        self,
        coordinator: ClaudeUsageCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the switch."""
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_auto_renew_session"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Claude Usage",
            manufacturer="Anthropic",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def is_on(self) -> bool:
        """Return true if session auto-renew is enabled."""
        return self._entry.options.get(CONF_AUTO_RENEW_SESSION, False)

    async def async_turn_on(self, **kwargs) -> None:
        """Enable session auto-renew."""
        self.hass.config_entries.async_update_entry(
            self._entry,
            options={**self._entry.options, CONF_AUTO_RENEW_SESSION: True},
        )
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Disable session auto-renew."""
        self.hass.config_entries.async_update_entry(
            self._entry,
            options={**self._entry.options, CONF_AUTO_RENEW_SESSION: False},
        )
        self.async_write_ha_state()

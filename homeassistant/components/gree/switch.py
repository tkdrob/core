"""Support for interface with a Gree climate systems."""
from __future__ import annotations

from homeassistant.components.switch import DEVICE_CLASS_SWITCH, SwitchEntity
from homeassistant.core import callback
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import COORDINATORS, DISPATCH_DEVICE_DISCOVERED, DISPATCHERS, DOMAIN


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Gree HVAC device from a config entry."""

    @callback
    def init_device(coordinator):
        """Register the device."""
        async_add_entities([GreeSwitchEntity(coordinator)])

    for coordinator in hass.data[DOMAIN][COORDINATORS]:
        init_device(coordinator)

    hass.data[DOMAIN][DISPATCHERS].append(
        async_dispatcher_connect(hass, DISPATCH_DEVICE_DISCOVERED, init_device)
    )


class GreeSwitchEntity(CoordinatorEntity, SwitchEntity):
    """Representation of a Gree HVAC device."""

    _attr_device_class = DEVICE_CLASS_SWITCH
    _attr_icon = "mdi:lightbulb"

    def __init__(self, coordinator):
        """Initialize the Gree device."""
        super().__init__(coordinator)
        self._attr_name = coordinator.device.device_info.name + " Panel Light"
        self._mac = coordinator.device.device_info.mac
        self._attr_unique_id = f"{self._mac}-panel-light"
        self._attr_device_info = {
            "name": coordinator.device.device_info.name + " Panel Light",
            "identifiers": {(DOMAIN, coordinator.device.device_info.mac)},
            "manufacturer": "Gree",
            "connections": {(CONNECTION_NETWORK_MAC, self._mac)},
        }

    @property
    def is_on(self) -> bool:
        """Return if the light is turned on."""
        return self.coordinator.device.light

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        self.coordinator.device.light = True
        await self.coordinator.push_state_update()
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        self.coordinator.device.light = False
        await self.coordinator.push_state_update()
        self.async_write_ha_state()

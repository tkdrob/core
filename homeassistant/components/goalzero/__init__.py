"""The Goal Zero Yeti integration."""
from __future__ import annotations

from goalzero import Yeti, exceptions

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_MODEL, CONF_HOST, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import GoalZeroDataUpdateCoordinator

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR, Platform.SWITCH]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Goal Zero Yeti from a config entry."""
    api = Yeti(entry.data[CONF_HOST], async_get_clientsession(hass))
    try:
        await api.init_connect()
    except exceptions.ConnectError as ex:
        raise ConfigEntryNotReady(f"Failed to connect to device: {ex}") from ex

    coordinator = GoalZeroDataUpdateCoordinator(hass, api, entry)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


class YetiEntity(CoordinatorEntity):
    """Representation of a Goal Zero Yeti entity."""

    _attr_attribution = "Data provided by Goal Zero"
    coordinator: GoalZeroDataUpdateCoordinator

    def __init__(self, coordinator: GoalZeroDataUpdateCoordinator) -> None:
        """Initialize a Goal Zero Yeti entity."""
        super().__init__(coordinator)

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device information of the entity."""
        return DeviceInfo(
            connections={
                (dr.CONNECTION_NETWORK_MAC, self.coordinator.api.sysdata["macAddress"])
            },
            identifiers={(DOMAIN, self.coordinator.config_entry.entry_id)},
            manufacturer=MANUFACTURER,
            model=self.coordinator.api.sysdata[ATTR_MODEL],
            name=self.coordinator.config_entry.title,
            sw_version=self.coordinator.api.data["firmwareVersion"],
        )

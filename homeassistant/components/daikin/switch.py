"""Support for Daikin AirBase zones."""
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity import ToggleEntity

from . import DOMAIN as DAIKIN_DOMAIN

ZONE_ICON = "mdi:home-circle"
STREAMER_ICON = "mdi:air-filter"
DAIKIN_ATTR_ADVANCED = "adv"
DAIKIN_ATTR_STREAMER = "streamer"


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Old way of setting up the platform.

    Can only be called when a user accidentally mentions the platform in their
    config. But even in that case it would have been ignored.
    """


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Daikin climate based on config_entry."""
    daikin_api = hass.data[DAIKIN_DOMAIN][entry.entry_id]
    switches = []
    zones = daikin_api.device.zones
    if zones:
        switches.extend(
            [
                DaikinZoneSwitch(daikin_api, zone_id)
                for zone_id, zone in enumerate(zones)
                if zone != ("-", "0")
            ]
        )
    if daikin_api.device.support_advanced_modes:
        # It isn't possible to find out from the API responses if a specific
        # device supports the streamer, so assume so if it does support
        # advanced modes.
        switches.append(DaikinStreamerSwitch(daikin_api))
    if switches:
        async_add_entities(switches)


class DaikinZoneSwitch(ToggleEntity):
    """Representation of a zone."""

    _attr_icon = ZONE_ICON

    def __init__(self, api, zone_id):
        """Initialize the zone."""
        self._api = api
        self._zone_id = zone_id
        self._attr_name = f"{api.name} {api.device.zones[zone_id][0]}"
        self._attr_unique_id = f"{api.device.mac}-zone{zone_id}"
        self._attr_device_info = api.device_info

    async def async_update(self):
        """Retrieve latest state."""
        await self._api.async_update()
        self._attr_is_on = self._api.device.zones[self._zone_id][1] == "1"

    async def async_turn_on(self, **kwargs):
        """Turn the zone on."""
        await self._api.device.set_zone(self._zone_id, "1")

    async def async_turn_off(self, **kwargs):
        """Turn the zone off."""
        await self._api.device.set_zone(self._zone_id, "0")


class DaikinStreamerSwitch(SwitchEntity):
    """Streamer state."""

    _attr_icon = STREAMER_ICON

    def __init__(self, api):
        """Initialize streamer switch."""
        self._api = api
        self._attr_name = f"{api.name} streamer"
        self._attr_unique_id = f"{api.device.mac}-streamer"
        self._attr_device_info = api.device_info

    async def async_update(self):
        """Retrieve latest state."""
        await self._api.async_update()
        self._attr_is_on = (
            DAIKIN_ATTR_STREAMER in self._api.device.represent(DAIKIN_ATTR_ADVANCED)[1]
        )

    async def async_turn_on(self, **kwargs):
        """Turn the zone on."""
        await self._api.device.set_streamer("on")

    async def async_turn_off(self, **kwargs):
        """Turn the zone off."""
        await self._api.device.set_streamer("off")

"""Support for EverLights lights."""
from __future__ import annotations

from datetime import timedelta
import logging

import pyeverlights
import voluptuous as vol

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    ATTR_HS_COLOR,
    PLATFORM_SCHEMA,
    SUPPORT_BRIGHTNESS,
    SUPPORT_COLOR,
    SUPPORT_EFFECT,
    LightEntity,
)
from homeassistant.const import CONF_HOSTS
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
import homeassistant.util.color as color_util

_LOGGER = logging.getLogger(__name__)

SUPPORT_EVERLIGHTS = SUPPORT_EFFECT | SUPPORT_BRIGHTNESS | SUPPORT_COLOR

SCAN_INTERVAL = timedelta(minutes=1)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {vol.Required(CONF_HOSTS): vol.All(cv.ensure_list, [cv.string])}
)


def color_rgb_to_int(red: int, green: int, blue: int) -> int:
    """Return a RGB color as an integer."""
    return red * 256 * 256 + green * 256 + blue


def color_int_to_rgb(value: int) -> tuple[int, int, int]:
    """Return an RGB tuple from an integer."""
    return (value >> 16, (value >> 8) & 0xFF, value & 0xFF)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the EverLights lights from configuration.yaml."""
    lights = []

    for ipaddr in config[CONF_HOSTS]:
        api = pyeverlights.EverLights(ipaddr, async_get_clientsession(hass))

        try:
            status = await api.get_status()

            effects = await api.get_all_patterns()

        except pyeverlights.ConnectionError as err:
            raise PlatformNotReady from err

        else:
            lights.append(EverLightsLight(api, pyeverlights.ZONE_1, status, effects))
            lights.append(EverLightsLight(api, pyeverlights.ZONE_2, status, effects))

    async_add_entities(lights, True)


class EverLightsLight(LightEntity):
    """Representation of a Flux light."""

    _attr_supported_features = SUPPORT_EVERLIGHTS

    def __init__(self, api, channel, status, effects):
        """Initialize the light."""
        self._api = api
        self._channel = channel
        self._status = status
        self._attr_effect_list = effects
        self._mac = status["mac"]
        self._error_reported = False
        self._hs_color = [255, 255]
        self._brightness = 255
        self._effect = None
        self._attr_unique_id = f"{status['mac']}-{channel}"
        self._attr_name = f"EverLights {status['mac']} Zone {channel}"

    async def async_turn_on(self, **kwargs):
        """Turn the light on."""
        hs_color = kwargs.get(ATTR_HS_COLOR, self._hs_color)
        brightness = kwargs.get(ATTR_BRIGHTNESS, self._brightness)
        effect = kwargs.get(ATTR_EFFECT)

        if effect is not None:
            colors = await self._api.set_pattern_by_id(self._channel, effect)

            rgb = color_int_to_rgb(colors[0])
            hsv = color_util.color_RGB_to_hsv(*rgb)
            hs_color = hsv[:2]
            brightness = hsv[2] / 100 * 255

        else:
            rgb = color_util.color_hsv_to_RGB(*hs_color, brightness / 255 * 100)
            colors = [color_rgb_to_int(*rgb)]

            await self._api.set_pattern(self._channel, colors)

        self._hs_color = hs_color
        self._brightness = brightness
        self._effect = effect

    async def async_turn_off(self, **kwargs):
        """Turn the light off."""
        await self._api.clear_pattern(self._channel)

    async def async_update(self):
        """Synchronize state with control box."""
        try:
            self._status = await self._api.get_status()
        except pyeverlights.ConnectionError:
            if self.available:
                _LOGGER.warning("EverLights control box connection lost")
            self._attr_available = False
        else:
            if not self.available:
                _LOGGER.warning("EverLights control box connection restored")
            self._attr_available = True
        self._attr_is_on = self._status[f"ch{self._channel}Active"] == 1
        self._attr_brightness = self._brightness
        self._attr_hs_color = self._hs_color
        self._attr_effect = self._effect

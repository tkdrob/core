"""Support for Eufy lights."""
import lakeside

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    ATTR_HS_COLOR,
    SUPPORT_BRIGHTNESS,
    SUPPORT_COLOR,
    SUPPORT_COLOR_TEMP,
    LightEntity,
)
import homeassistant.util.color as color_util
from homeassistant.util.color import (
    color_temperature_kelvin_to_mired as kelvin_to_mired,
    color_temperature_mired_to_kelvin as mired_to_kelvin,
)

EUFY_MAX_KELVIN = 6500
EUFY_MIN_KELVIN = 2700


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up Eufy bulbs."""
    if discovery_info is None:
        return
    add_entities([EufyLight(discovery_info)], True)


class EufyLight(LightEntity):
    """Representation of a Eufy light."""

    _attr_max_mireds = kelvin_to_mired(EUFY_MAX_KELVIN)
    _attr_min_mireds = kelvin_to_mired(EUFY_MIN_KELVIN)

    def __init__(self, device):
        """Initialize the light."""

        self._temp = None
        self._hs = None
        self._attr_name = device["name"]
        self._attr_unique_id = device["address"]
        self._bulb = lakeside.bulb(device["address"], device["code"], device["type"])
        self._colormode = False
        if device["type"] == "T1011":
            self._attr_supported_features = SUPPORT_BRIGHTNESS
        elif device["type"] == "T1012":
            self._attr_supported_features = SUPPORT_BRIGHTNESS | SUPPORT_COLOR_TEMP
        elif device["type"] == "T1013":
            self._attr_supported_features = (
                SUPPORT_BRIGHTNESS | SUPPORT_COLOR_TEMP | SUPPORT_COLOR
            )
        self._bulb.connect()

    def update(self):
        """Synchronise state from the bulb."""
        self._bulb.update()
        if self._bulb.power:
            self._attr_brightness = int(self._bulb.brightness * 255 / 100)
            self._temp = self._bulb.temperature
            if self._bulb.colors:
                self._colormode = True
                self._hs = color_util.color_RGB_to_hs(*self._bulb.colors)
            else:
                self._colormode = False
            self._attr_hs_color = None
            if self._colormode:
                self._attr_hs_color = self._hs
        self._attr_is_on = self._bulb.power
        temp_in_k = int(
            EUFY_MIN_KELVIN + (self._temp * (EUFY_MAX_KELVIN - EUFY_MIN_KELVIN) / 100)
        )
        self._attr_color_temp = kelvin_to_mired(temp_in_k)

    def turn_on(self, **kwargs):
        """Turn the specified light on."""
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        colortemp = kwargs.get(ATTR_COLOR_TEMP)
        # pylint: disable=invalid-name
        hs = kwargs.get(ATTR_HS_COLOR)

        if brightness is not None:
            brightness = int(brightness * 100 / 255)
        else:
            if self.brightness is None:
                self._attr_brightness = 100
            brightness = self.brightness

        temp = None
        if colortemp is not None:
            self._colormode = False
            temp_in_k = mired_to_kelvin(colortemp)
            relative_temp = temp_in_k - EUFY_MIN_KELVIN
            temp = int(relative_temp * 100 / (EUFY_MAX_KELVIN - EUFY_MIN_KELVIN))

        rgb = None
        if hs is not None:
            rgb = color_util.color_hsv_to_RGB(hs[0], hs[1], brightness / 255 * 100)
            self._colormode = True
        elif self._colormode:
            rgb = color_util.color_hsv_to_RGB(
                self._hs[0], self._hs[1], brightness / 255 * 100
            )

        try:
            self._bulb.set_state(
                power=True, brightness=brightness, temperature=temp, colors=rgb
            )
        except BrokenPipeError:
            self._bulb.connect()
            self._bulb.set_state(
                power=True, brightness=brightness, temperature=temp, colors=rgb
            )

    def turn_off(self, **kwargs):
        """Turn the specified light off."""
        try:
            self._bulb.set_state(power=False)
        except BrokenPipeError:
            self._bulb.connect()
            self._bulb.set_state(power=False)

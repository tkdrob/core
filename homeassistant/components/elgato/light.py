"""Support for Elgato lights."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from elgato import Elgato, ElgatoError, Info, Settings, State

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    ATTR_HS_COLOR,
    COLOR_MODE_COLOR_TEMP,
    COLOR_MODE_HS,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_IDENTIFIERS,
    ATTR_MANUFACTURER,
    ATTR_MODEL,
    ATTR_NAME,
    ATTR_SW_VERSION,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import (
    AddEntitiesCallback,
    async_get_current_platform,
)

from .const import DATA_ELGATO_CLIENT, DOMAIN, SERVICE_IDENTIFY

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 1
SCAN_INTERVAL = timedelta(seconds=10)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Elgato Light based on a config entry."""
    elgato: Elgato = hass.data[DOMAIN][entry.entry_id][DATA_ELGATO_CLIENT]
    info = await elgato.info()
    settings = await elgato.settings()
    async_add_entities([ElgatoLight(elgato, info, settings)], True)

    platform = async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_IDENTIFY,
        {},
        ElgatoLight.async_identify.__name__,
    )


class ElgatoLight(LightEntity):
    """Defines an Elgato Light."""

    def __init__(self, elgato: Elgato, info: Info, settings: Settings) -> None:
        """Initialize Elgato Light."""
        self._state: State | None = None
        self.elgato = elgato

        self._attr_min_mireds = 143
        self._attr_max_mireds = 344
        self._attr_supported_color_modes = {COLOR_MODE_COLOR_TEMP}

        # Elgato Light supporting color, have a different temperature range
        if settings.power_on_hue is not None:
            self._attr_supported_color_modes = {COLOR_MODE_COLOR_TEMP, COLOR_MODE_HS}
            self._attr_min_mireds = 153
            self._attr_max_mireds = 285

        self._attr_name = info.display_name or info.product_name
        self._attr_unique_id = info.serial_number
        self._attr_device_info = {
            ATTR_IDENTIFIERS: {(DOMAIN, info.serial_number)},
            ATTR_NAME: info.product_name,
            ATTR_MANUFACTURER: "Elgato",
            ATTR_MODEL: info.product_name,
            ATTR_SW_VERSION: f"{info.firmware_version} ({info.firmware_build_number})",
        }

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light."""
        try:
            await self.elgato.light(on=False)
        except ElgatoError:
            _LOGGER.error("An error occurred while updating the Elgato Light")
            self._state = None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light."""
        temperature = kwargs.get(ATTR_COLOR_TEMP)

        hue = None
        saturation = None
        if ATTR_HS_COLOR in kwargs:
            hue, saturation = kwargs[ATTR_HS_COLOR]

        brightness = None
        if ATTR_BRIGHTNESS in kwargs:
            brightness = round((kwargs[ATTR_BRIGHTNESS] / 255) * 100)

        # For Elgato lights supporting color mode, but in temperature mode;
        # adjusting only brightness make them jump back to color mode.
        # Resending temperature prevents that.
        if (
            brightness
            and ATTR_HS_COLOR not in kwargs
            and ATTR_COLOR_TEMP not in kwargs
            and self.supported_color_modes
            and COLOR_MODE_HS in self.supported_color_modes
            and self.color_mode == COLOR_MODE_COLOR_TEMP
        ):
            temperature = self.color_temp

        try:
            await self.elgato.light(
                on=True,
                brightness=brightness,
                hue=hue,
                saturation=saturation,
                temperature=temperature,
            )
        except ElgatoError:
            _LOGGER.error("An error occurred while updating the Elgato Light")
            self._state = None

    async def async_update(self) -> None:
        """Update Elgato entity."""
        restoring = self._state is None
        try:
            self._state = await self.elgato.state()
            if restoring:
                _LOGGER.info("Connection restored")
        except ElgatoError as err:
            meth = _LOGGER.error if self._state else _LOGGER.debug
            meth("An error occurred while updating the Elgato Light: %s", err)
            self._state = None
        self._attr_available = self._state is not None
        if self._state is not None:
            self._attr_is_on = self._state.on
            self._attr_brightness = round((self._state.brightness * 255) / 100)
            self._attr_color_temp = self._state.temperature
            self._attr_color_mode = COLOR_MODE_COLOR_TEMP
            if self._state.hue is not None:
                self._attr_color_mode = COLOR_MODE_HS
        if (
            self._state is None
            or self._state.hue is None
            or self._state.saturation is None
        ):
            self._attr_hs_color = None
        else:
            self._attr_hs_color = (self._state.hue, self._state.saturation)

    async def async_identify(self) -> None:
        """Identify the light, will make it blink."""
        try:
            await self.elgato.identify()
        except ElgatoError:
            _LOGGER.exception("An error occurred while identifying the Elgato Light")
            self._state = None

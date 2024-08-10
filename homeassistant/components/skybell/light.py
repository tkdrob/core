"""Light/LED support for the Skybell HD Doorbell."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
import dataclasses
from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_RGB_COLOR,
    ColorMode,
    LightEntity,
    LightEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api.device import SkybellDevice
from .coordinator import SkybellConfigEntry
from .entity import SkybellEntity


@dataclasses.dataclass(frozen=True, kw_only=True)
class SkybellLightEntityDescription(LightEntityDescription):
    """Class to describe a Skybell light."""

    brightness_fn: Callable[[SkybellDevice], int]
    is_on_fn: Callable[[SkybellDevice], bool]
    rgb_color_fn: Callable[[SkybellDevice], tuple[int, int, int]]
    translation_key: str
    turn_off_fn: Callable[[SkybellDevice], Awaitable]


LIGHT_TYPE = SkybellLightEntityDescription(
    key="light",
    translation_key="led_color",
    brightness_fn=lambda d: int(d.info.settings.led_color_brightness / 150 * 255),
    is_on_fn=lambda d: any(c for c in d.info.settings.led_color),
    rgb_color_fn=lambda d: d.info.settings.led_color,
    turn_off_fn=lambda d: d.set_settings(led_color=(0, 0, 0)),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SkybellConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Skybell switch."""

    async_add_entities(
        SkybellLight(coordinator, LIGHT_TYPE)
        for coordinator in entry.runtime_data.devices
        if not coordinator.device.info.shared_read_only
    )


class SkybellLight(SkybellEntity, LightEntity):
    """A light implementation for Skybell devices."""

    _attr_color_mode = ColorMode.RGB
    _attr_supported_color_modes = {ColorMode.RGB}
    entity_description: SkybellLightEntityDescription

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the light."""
        key = self.entity_description.translation_key
        data = {}
        if color := kwargs.get(ATTR_RGB_COLOR):
            data[key] = color
        if brightness := kwargs.get(ATTR_BRIGHTNESS):
            if not data:
                data[key] = self.entity_description.rgb_color_fn(self._device)
            data[f"{key}_brightness"] = brightness
        if not kwargs:
            data[key] = (255, 255, 255)

        await self._device.set_settings(**data)
        self.coordinator.async_set_updated_data(None)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the light."""
        await self.entity_description.turn_off_fn(self._device)
        self.coordinator.async_set_updated_data(None)

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        return self.entity_description.is_on_fn(self._device)

    @property
    def brightness(self) -> int:
        """Return the brightness of the light."""
        return self.entity_description.brightness_fn(self._device)

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        """Return the rgb color value [int, int, int]."""
        return self.entity_description.rgb_color_fn(self._device)

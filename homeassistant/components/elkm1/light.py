"""Support for control of ElkM1 lighting (X10, UPB, etc)."""

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    SUPPORT_BRIGHTNESS,
    LightEntity,
)

from . import ElkEntity, create_elk_entities
from .const import DOMAIN


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Elk light platform."""
    elk_data = hass.data[DOMAIN][config_entry.entry_id]
    entities = []
    elk = elk_data["elk"]
    create_elk_entities(elk_data, elk.lights, "plc", ElkLight, entities)
    async_add_entities(entities, True)


class ElkLight(ElkEntity, LightEntity):
    """Representation of an Elk lighting device."""

    _attr_supported_features = SUPPORT_BRIGHTNESS

    def __init__(self, element, elk, elk_data):
        """Initialize the Elk light."""
        super().__init__(element, elk, elk_data)
        self._attr_brightness = self._element.status

    def _element_changed(self, element, changeset):
        status = self._element.status if self._element.status != 1 else 100
        self._attr_brightness = round(status * 2.55)
        self._attr_is_on = self.brightness != 0

    async def async_turn_on(self, **kwargs):
        """Turn on the light."""
        self._element.level(round(kwargs.get(ATTR_BRIGHTNESS, 255) / 2.55))

    async def async_turn_off(self, **kwargs):
        """Turn off the light."""
        self._element.level(0)

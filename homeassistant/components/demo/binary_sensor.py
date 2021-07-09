"""Demo platform that has two fake binary sensors."""
from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_MOISTURE,
    DEVICE_CLASS_MOTION,
    BinarySensorEntity,
)

from . import DOMAIN


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Demo binary sensor platform."""
    async_add_entities(
        [
            DemoBinarySensor(
                "binary_1", "Basement Floor Wet", False, DEVICE_CLASS_MOISTURE
            ),
            DemoBinarySensor(
                "binary_2", "Movement Backyard", True, DEVICE_CLASS_MOTION
            ),
        ]
    )


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Demo config entry."""
    await async_setup_platform(hass, {}, async_add_entities)


class DemoBinarySensor(BinarySensorEntity):
    """representation of a Demo binary sensor."""

    _attr_should_poll = False

    def __init__(self, unique_id, name, state, device_class):
        """Initialize the demo sensor."""
        self._attr_unique_id = unique_id
        self._attr_name = name
        self._state = state
        self._attr_device_class = device_class
        self._attr_device_info = {
            "identifiers": {
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.unique_id)
            },
            "name": self.name,
        }

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return self._state

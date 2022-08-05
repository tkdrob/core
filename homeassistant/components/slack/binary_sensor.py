"""Binary sensor support for the Slack integration."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import DOMAIN
from .entity import SlackEntity

BINARY_SENSOR_TYPES: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(
        key="huddle", name="Huddle", device_class=BinarySensorDeviceClass.CONNECTIVITY
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Slack switch."""
    async_add_entities(
        SlackBinarySensor(hass.data[DOMAIN][entry.entry_id], description)
        for description in BINARY_SENSOR_TYPES
    )


class SlackBinarySensor(SlackEntity, BinarySensorEntity):
    """A binary sensor implementation for Slack."""

    @property
    def is_on(self) -> bool:
        """Return True if the binary sensor is on."""
        return self.coordinator.profile["huddle_state"] != "default_unset"

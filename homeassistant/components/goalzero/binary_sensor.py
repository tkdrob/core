"""Support for Goal Zero Yeti Sensors."""
from __future__ import annotations

from typing import cast

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import YetiEntity
from .const import DOMAIN
from .coordinator import GoalZeroDataUpdateCoordinator

PARALLEL_UPDATES = 0

BINARY_SENSOR_TYPES: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(
        key="backlight",
        name="Backlight",
        icon="mdi:clock-digital",
    ),
    BinarySensorEntityDescription(
        key="app_online",
        name="App Online",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    BinarySensorEntityDescription(
        key="isCharging",
        name="Charging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
    ),
    BinarySensorEntityDescription(
        key="inputDetected",
        name="Input Detected",
        device_class=BinarySensorDeviceClass.POWER,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Goal Zero Yeti sensor."""
    async_add_entities(
        YetiBinarySensor(hass.data[DOMAIN][entry.entry_id], description)
        for description in BINARY_SENSOR_TYPES
    )


class YetiBinarySensor(YetiEntity, BinarySensorEntity):
    """Representation of a Goal Zero Yeti sensor."""

    coordinator: GoalZeroDataUpdateCoordinator

    def __init__(
        self,
        coordinator: GoalZeroDataUpdateCoordinator,
        description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize a Goal Zero Yeti sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_name = f"{coordinator.config_entry.title} {description.name}"
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}/{description.key}"

    @property
    def is_on(self) -> bool:
        """Return True if the service is on."""
        return cast(bool, self.coordinator.api.data[self.entity_description.key] == 1)

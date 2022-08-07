"""Support for monitoring Dremel 3D Printer binary sensors."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast

from dremel3dpy import Dremel3DPrinter

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, LOGGER
from .entity import Dremel3DPrinterEntity


@dataclass
class Dremel3DPrinterBinarySensorEntityMixin:
    """Mixin for Dremel 3D Printer binary sensor."""

    value_fn: Callable[[Dremel3DPrinter], bool]


@dataclass
class Dremel3DPrinterBinarySensorEntityDescription(
    BinarySensorEntityDescription, Dremel3DPrinterBinarySensorEntityMixin
):
    """Describes a Dremel 3D Printer binary sensor."""


BINARY_SENSOR_TYPES: tuple[Dremel3DPrinterBinarySensorEntityDescription, ...] = (
    Dremel3DPrinterBinarySensorEntityDescription(
        key="door_contact",
        name="Door contact",
        device_class=BinarySensorDeviceClass.DOOR,
        value_fn=lambda api: cast(bool, api.is_door_open()),
    ),
    Dremel3DPrinterBinarySensorEntityDescription(
        key="running",
        name="Running",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda api: cast(bool, api.is_running()),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the available Dremel binary sensors."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    async_add_entities(
        Dremel3DPrinterBinarySensor(coordinator, description)
        for description in BINARY_SENSOR_TYPES
    )


class Dremel3DPrinterBinarySensor(Dremel3DPrinterEntity, BinarySensorEntity):
    """Representation of a Dremel 3D Printer door binary sensor."""

    entity_description: Dremel3DPrinterBinarySensorEntityDescription

    @property
    def is_on(self) -> bool:
        """Return true if door is open."""
        return self.entity_description.value_fn(self._api)

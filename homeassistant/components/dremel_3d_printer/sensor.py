"""Support for monitoring Dremel 3D Printer sensors."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast

from dremel3dpy import Dremel3DPrinter

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, TEMP_CELSIUS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import DOMAIN
from .entity import Dremel3DPrinterEntity


@dataclass
class Dremel3DPrinterSensorEntityMixin:
    """Mixin for Dremel 3D Printer sensor."""

    value_fn: Callable[[Dremel3DPrinter, str], StateType]


@dataclass
class Dremel3DPrinterSensorEntityDescription(
    SensorEntityDescription, Dremel3DPrinterSensorEntityMixin
):
    """Describes a Dremel 3D Printer sensor."""


SENSOR_TYPES: tuple[Dremel3DPrinterSensorEntityDescription, ...] = (
    Dremel3DPrinterSensorEntityDescription(
        key="job_phase",
        name="Job phase",
        value_fn=lambda api, _: cast(str, api.get_printing_status()),
    ),
    Dremel3DPrinterSensorEntityDescription(
        key="progress",
        name="Progress",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda api, _: cast(float, api.get_printing_progress()),
    ),
    Dremel3DPrinterSensorEntityDescription(
        key="chamber",
        name="Chamber",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=TEMP_CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda api, type: cast(int, api.get_temperature_type(type)),
    ),
    Dremel3DPrinterSensorEntityDescription(
        key="platform",
        name="Platform",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=TEMP_CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda api, type: cast(int, api.get_temperature_type(type)),
    ),
    Dremel3DPrinterSensorEntityDescription(
        key="extruder",
        name="Extruder",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=TEMP_CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda api, type: cast(int, api.get_temperature_type(type)),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the available Dremel 3D Printer sensors."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    async_add_entities(
        Dremel3DPrinterSensor(coordinator, description) for description in SENSOR_TYPES
    )


class Dremel3DPrinterSensor(Dremel3DPrinterEntity, SensorEntity):
    """Representation of an Dremel 3D Printer sensor."""

    entity_description: Dremel3DPrinterSensorEntityDescription

    @property
    def native_value(self) -> StateType:
        """Return temperature sensor state."""
        return self.entity_description.value_fn(self._api, self.entity_description.key)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return job related attributes for this status sensor."""
        if self.entity_description.key == "job_phase":
            return self._api.get_printing_attributes()  # type: ignore[no-any-return]
        if self.entity_description.key in ("platform", "extruder"):
            return self._api.get_temperature_attributes(self.entity_description.key)  # type: ignore[no-any-return]
        return {}

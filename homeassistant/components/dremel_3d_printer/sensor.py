"""Support for monitoring Dremel 3D Printer sensors."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import cast

from dremel3dpy import Dremel3DPrinter

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, TEMP_CELSIUS, TIME_HOURS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import ATTR_EXTRUDER, ATTR_PLATFORM, DOMAIN
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
        icon="mdi:printer-3d",
        value_fn=lambda api, _: cast(str, api.get_printing_status()),
    ),
    Dremel3DPrinterSensorEntityDescription(
        key="remaining_time",
        name="Remaining time",  # TODO determine time in seconds or minutes
        icon="mdi:clock",
        value_fn=lambda api, _: cast(int, api.get_job_status()["remaining_time"]),
    ),
    Dremel3DPrinterSensorEntityDescription(
        key="progress",
        name="Progress",
        icon="mdi:printer-3d-nozzle",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda api, _: cast(float, api.get_printing_progress()),
    ),
    Dremel3DPrinterSensorEntityDescription(
        key="chamber",
        name="Chamber",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=TEMP_CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda api, type: cast(int, api.get_temperature_type(type)),
    ),
    Dremel3DPrinterSensorEntityDescription(
        key=ATTR_PLATFORM,
        name="Platform",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=TEMP_CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda api, type: cast(int, api.get_temperature_type(type)),
    ),
    Dremel3DPrinterSensorEntityDescription(
        key="target_platform_temperature",
        name="Target platform temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=TEMP_CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda api, _: cast(
            int, api.get_temperature_attributes(ATTR_PLATFORM)["target_temp"]
        ),
    ),
    Dremel3DPrinterSensorEntityDescription(
        key="max_platform_temperature",
        name="Max platform temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=TEMP_CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda api, _: cast(
            int, api.get_temperature_attributes(ATTR_PLATFORM)["max_temp"]
        ),
    ),
    Dremel3DPrinterSensorEntityDescription(
        key=ATTR_EXTRUDER,
        name="Extruder",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=TEMP_CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda api, type: cast(int, api.get_temperature_type(type)),
    ),
    Dremel3DPrinterSensorEntityDescription(
        key="target_extruder_temperature",
        name="Target extruder temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=TEMP_CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda api, _: cast(
            int, api.get_temperature_attributes(ATTR_EXTRUDER)["target_temp"]
        ),
    ),
    Dremel3DPrinterSensorEntityDescription(
        key="max_extruder_temperature",
        name="Max extruder temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=TEMP_CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda api, _: cast(
            int, api.get_temperature_attributes(ATTR_EXTRUDER)["max_temp"]
        ),
    ),
    Dremel3DPrinterSensorEntityDescription(
        key="fan_speed",
        name="Fan Speed",
        icon="mdi:clock",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda api, _: cast(int, api.get_job_status()["fan_speed"]),
    ),
    Dremel3DPrinterSensorEntityDescription(
        key="network_build",
        name="Network build",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda api, _: cast(int, api.get_job_status()["network_build"]),
    ),
    Dremel3DPrinterSensorEntityDescription(
        key="filament",
        name="Filament",
        icon="mdi:printer-3d-nozzle",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda api, _: cast(str, api.get_job_status()["filament"]),
    ),
    Dremel3DPrinterSensorEntityDescription(
        key="elapsed_time",
        name="Elapsed time",  # TODO determine time in seconds or minutes
        icon="mdi:clock",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda api, _: cast(int, api.get_job_status()["elapsed_time"]),
    ),
    Dremel3DPrinterSensorEntityDescription(
        key="estimated_total_time",
        name="Estimated total time",  # TODO determine time in seconds or minutes
        icon="mdi:clock",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda api, _: cast(int, api.get_job_status()["estimated_total_time"]),
    ),
    Dremel3DPrinterSensorEntityDescription(
        key="job_status",
        name="Job status",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda api, _: cast(str, api.get_job_status()["job_status"]),
    ),
    Dremel3DPrinterSensorEntityDescription(
        key="job_name",
        name="Job name",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda api, _: cast(str, api.get_job_name()),
    ),
    Dremel3DPrinterSensorEntityDescription(
        key="api_version",
        name="API version",
        icon="mdi:api",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda api, _: cast(str, api.get_printer_info()["api_version"]),
    ),
    Dremel3DPrinterSensorEntityDescription(
        key="ip",
        name="IP",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda api, _: cast(str, api.get_printer_info()["host"]),
    ),
    Dremel3DPrinterSensorEntityDescription(
        key="connection_type",
        name="Connection type",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda api, _: cast(str, api.get_printer_info()["connection_type"]),
    ),
    Dremel3DPrinterSensorEntityDescription(
        key="machine_type",
        name="Machine type",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda api, _: cast(str, api.get_printer_info()["machine_type"]),
    ),
    Dremel3DPrinterSensorEntityDescription(
        key="serial_number",
        name="Serial Number",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda api, _: cast(str, api.get_printer_info()["SN"]),
    ),
    Dremel3DPrinterSensorEntityDescription(
        key="available_storage",
        name="Available storage",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda api, _: cast(str, api.get_printer_info()["available_storage"]),
    ),
    Dremel3DPrinterSensorEntityDescription(
        key="hours_used",
        name="Hours used",
        icon="mdi:clock",
        native_unit_of_measurement=TIME_HOURS,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda api, _: cast(str, api.get_printer_info()["hours_used"]),
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

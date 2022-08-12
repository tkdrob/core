"""Support for Abode Security System sensors."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import cast

from abodepy.devices.sensor import CONST, AbodeSensor as AbodeSense

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import AbodeDevice, AbodeSystem
from .const import DOMAIN


@dataclass
class AbodeSensorEntityDescriptionMixin:
    """Mixin for Abode sensor entities."""

    unit_fn: Callable[[AbodeSense], str]
    value_fn: Callable[[AbodeSense], float]


@dataclass
class AbodeSensorEntityDescription(
    SensorEntityDescription, AbodeSensorEntityDescriptionMixin
):
    """Class describing abode sensor entities."""


SENSOR_TYPES: tuple[AbodeSensorEntityDescription, ...] = (
    AbodeSensorEntityDescription(
        key=CONST.TEMP_STATUS_KEY,
        name="Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        unit_fn=lambda device: cast(str, device.temp_unit),
        value_fn=lambda device: cast(float, device.temp),
    ),
    AbodeSensorEntityDescription(
        key=CONST.HUMI_STATUS_KEY,
        name="Humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        unit_fn=lambda device: cast(str, device.humidity_unit),
        value_fn=lambda device: cast(float, device.humidity),
    ),
    AbodeSensorEntityDescription(
        key=CONST.LUX_STATUS_KEY,
        name="Lux",
        device_class=SensorDeviceClass.ILLUMINANCE,
        unit_fn=lambda device: cast(str, device.lux_unit),
        value_fn=lambda device: cast(float, device.lux),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Abode sensor devices."""
    data: AbodeSystem = hass.data[DOMAIN]

    async_add_entities(
        AbodeSensor(data, device, description)
        for description in SENSOR_TYPES
        for device in data.abode.get_devices(generic_type=CONST.TYPE_SENSOR)
        if description.key in device.get_value(CONST.STATUSES_KEY)
    )


class AbodeSensor(AbodeDevice, SensorEntity):
    """A sensor implementation for Abode devices."""

    _device: AbodeSense
    entity_description: AbodeSensorEntityDescription

    def __init__(
        self,
        data: AbodeSystem,
        device: AbodeSense,
        description: AbodeSensorEntityDescription,
    ) -> None:
        """Initialize a sensor for an Abode device."""
        super().__init__(data, device)
        self.entity_description = description
        self._attr_name = f"{device.name} {description.name}"
        self._attr_unique_id = f"{device.device_uuid}-{description.key}"
        self._attr_native_unit_of_measurement = description.unit_fn(device)

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self._device)

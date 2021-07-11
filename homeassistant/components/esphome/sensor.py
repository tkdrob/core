"""Support for esphome sensors."""
from __future__ import annotations

import math

from aioesphomeapi import (
    SensorInfo,
    SensorState,
    SensorStateClass,
    TextSensorInfo,
    TextSensorState,
)
import voluptuous as vol

from homeassistant.components.sensor import (
    DEVICE_CLASS_TIMESTAMP,
    DEVICE_CLASSES,
    STATE_CLASS_MEASUREMENT,
    SensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.util import dt

from . import (
    EsphomeEntity,
    EsphomeEnumMapper,
    esphome_state_property,
    platform_async_setup_entry,
)

ICON_SCHEMA = vol.Schema(cv.icon)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up esphome sensors based on a config entry."""
    await platform_async_setup_entry(
        hass,
        entry,
        async_add_entities,
        component_key="sensor",
        info_type=SensorInfo,
        entity_type=EsphomeSensor,
        state_type=SensorState,
    )
    await platform_async_setup_entry(
        hass,
        entry,
        async_add_entities,
        component_key="text_sensor",
        info_type=TextSensorInfo,
        entity_type=EsphomeTextSensor,
        state_type=TextSensorState,
    )


# https://github.com/PyCQA/pylint/issues/3150 for all @esphome_state_property
# pylint: disable=invalid-overridden-method


_STATE_CLASSES: EsphomeEnumMapper[SensorStateClass] = EsphomeEnumMapper(
    {
        SensorStateClass.NONE: None,
        SensorStateClass.MEASUREMENT: STATE_CLASS_MEASUREMENT,
    }
)


class EsphomeSensor(EsphomeEntity, SensorEntity):
    """A sensor implementation for esphome."""

    def __init__(self, entry_data, component_key: str, key: int) -> None:
        """Initialize a sensor implementation for esphome."""
        super().__init__(entry_data, component_key, key)
        if not self._static_info.icon or self._static_info.device_class:
            self._attr_icon = None
        else:
            self._attr_icon = ICON_SCHEMA(self._static_info.icon)
        if self._static_info.unit_of_measurement:
            self._attr_unit_of_measurement = self._static_info.unit_of_measurement
        if self._static_info.device_class in DEVICE_CLASSES:
            self._attr_device_class = self._static_info.device_class
        if self._static_info.state_class:
            self._attr_state_class = _STATE_CLASSES.from_esphome(
                self._static_info.state_class
            )

    @property
    def _static_info(self) -> SensorInfo:
        return super()._static_info

    @property
    def _state(self) -> SensorState | None:
        return super()._state

    @property
    def force_update(self) -> bool:
        """Return if this sensor should force a state update."""
        return self._static_info.force_update

    @esphome_state_property
    def state(self) -> str | None:
        """Return the state of the entity."""
        if math.isnan(self._state.state):
            return None
        if self._state.missing_state:
            return None
        if self.device_class == DEVICE_CLASS_TIMESTAMP:
            return dt.utc_from_timestamp(self._state.state).isoformat()
        return f"{self._state.state:.{self._static_info.accuracy_decimals}f}"


class EsphomeTextSensor(EsphomeEntity, SensorEntity):
    """A text sensor implementation for ESPHome."""

    @property
    def _static_info(self) -> TextSensorInfo:
        return super()._static_info

    @property
    def _state(self) -> TextSensorState | None:
        return super()._state

    @property
    def icon(self) -> str:
        """Return the icon."""
        return self._static_info.icon

    @esphome_state_property
    def state(self) -> str | None:
        """Return the state of the entity."""
        if self._state.missing_state:
            return None
        return self._state.state

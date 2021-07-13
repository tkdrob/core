"""Support for Freebox devices (Freebox v6 and Freebox mini 4K)."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import DATA_RATE_KILOBYTES_PER_SECOND
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
import homeassistant.util.dt as dt_util

from .const import (
    CALL_SENSORS,
    CONNECTION_SENSORS,
    DISK_PARTITION_SENSORS,
    DOMAIN,
    SENSOR_DEVICE_CLASS,
    SENSOR_ICON,
    SENSOR_NAME,
    SENSOR_UNIT,
    TEMPERATURE_SENSOR_TEMPLATE,
)
from .router import FreeboxRouter

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up the sensors."""
    router = hass.data[DOMAIN][entry.unique_id]
    entities = []

    _LOGGER.debug(
        "%s - %s - %s temperature sensors",
        router.name,
        router.mac,
        len(router.sensors_temperature),
    )
    for sensor_name in router.sensors_temperature:
        entities.append(
            FreeboxSensor(
                router,
                sensor_name,
                {**TEMPERATURE_SENSOR_TEMPLATE, SENSOR_NAME: f"Freebox {sensor_name}"},
            )
        )

    for sensor_key in CONNECTION_SENSORS:
        entities.append(
            FreeboxSensor(router, sensor_key, CONNECTION_SENSORS[sensor_key])
        )

    for sensor_key in CALL_SENSORS:
        entities.append(FreeboxCallSensor(router, sensor_key, CALL_SENSORS[sensor_key]))

    _LOGGER.debug("%s - %s - %s disk(s)", router.name, router.mac, len(router.disks))
    for disk in router.disks.values():
        for partition in disk["partitions"]:
            for sensor_key in DISK_PARTITION_SENSORS:
                entities.append(
                    FreeboxDiskSensor(
                        router,
                        disk,
                        partition,
                        sensor_key,
                        DISK_PARTITION_SENSORS[sensor_key],
                    )
                )

    async_add_entities(entities, True)


class FreeboxSensor(SensorEntity):
    """Representation of a Freebox sensor."""

    _attr_should_poll = False

    def __init__(
        self, router: FreeboxRouter, sensor_type: str, sensor: dict[str, Any]
    ) -> None:
        """Initialize a Freebox sensor."""
        self._router = router
        self._sensor_type = sensor_type
        self._attr_name = sensor[SENSOR_NAME]
        self._attr_unit_of_measurement = sensor[SENSOR_UNIT]
        self._attr_icon = sensor[SENSOR_ICON]
        self._attr_device_class = sensor[SENSOR_DEVICE_CLASS]
        self._attr_unique_id = f"{router.mac} {sensor[SENSOR_NAME]}"

    @callback
    def async_update_state(self) -> None:
        """Update the Freebox sensor."""
        state = self._router.sensors[self._sensor_type]
        self._attr_device_info = self._router.device_info
        if self._attr_unit_of_measurement == DATA_RATE_KILOBYTES_PER_SECOND:
            self._attr_state = round(state / 1000, 2)
        else:
            self._attr_state = state

    @callback
    def async_on_demand_update(self):
        """Update state."""
        self.async_update_state()
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Register state update callback."""
        self.async_update_state()
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                self._router.signal_sensor_update,
                self.async_on_demand_update,
            )
        )


class FreeboxCallSensor(FreeboxSensor):
    """Representation of a Freebox call sensor."""

    def __init__(
        self, router: FreeboxRouter, sensor_type: str, sensor: dict[str, Any]
    ) -> None:
        """Initialize a Freebox call sensor."""
        super().__init__(router, sensor_type, sensor)
        self._call_list_for_type = []

    @callback
    def async_update_state(self) -> None:
        """Update the Freebox call sensor."""
        self._call_list_for_type = []
        if self._router.call_list:
            for call in self._router.call_list:
                if not call["new"]:
                    continue
                if call["type"] == self._sensor_type:
                    self._call_list_for_type.append(call)

        self._attr_state = len(self._call_list_for_type)
        self._attr_extra_state_attributes = {
            dt_util.utc_from_timestamp(call["datetime"]).isoformat(): call["name"]
            for call in self._call_list_for_type
        }


class FreeboxDiskSensor(FreeboxSensor):
    """Representation of a Freebox disk sensor."""

    def __init__(
        self,
        router: FreeboxRouter,
        disk: dict[str, Any],
        partition: dict[str, Any],
        sensor_type: str,
        sensor: dict[str, Any],
    ) -> None:
        """Initialize a Freebox disk sensor."""
        super().__init__(router, sensor_type, sensor)
        self._partition = partition
        self._attr_name = f"{partition['label']} {sensor[SENSOR_NAME]}"
        self._attr_unique_id = (
            f"{self._router.mac} {sensor_type} {disk['id']} {partition['id']}"
        )
        self._attr_device_info = {
            "identifiers": {(DOMAIN, disk["id"])},
            "name": f"Disk {disk['id']}",
            "model": disk["model"],
            "sw_version": disk["firmware"],
            "via_device": (
                DOMAIN,
                self._router.mac,
            ),
        }

    @callback
    def async_update_state(self) -> None:
        """Update the Freebox disk sensor."""
        self._attr_state = round(
            self._partition["free_bytes"] * 100 / self._partition["total_bytes"], 2
        )

"""Support for the Hive sesnors."""

from datetime import timedelta

from homeassistant.components.sensor import DEVICE_CLASS_BATTERY, SensorEntity
from homeassistant.const import (
    ATTR_IDENTIFIERS,
    ATTR_MANUFACTURER,
    ATTR_MODEL,
    ATTR_NAME,
    ATTR_SW_VERSION,
)

from . import HiveEntity
from .const import DOMAIN

PARALLEL_UPDATES = 0
SCAN_INTERVAL = timedelta(seconds=15)
DEVICETYPE = {
    "Battery": {"unit": " % ", "type": DEVICE_CLASS_BATTERY},
}


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Hive thermostat based on a config entry."""

    hive = hass.data[DOMAIN][entry.entry_id]
    devices = hive.session.deviceList.get("sensor")
    entities = []
    if devices:
        for dev in devices:
            entities.append(HiveSensorEntity(hive, dev))
    async_add_entities(entities, True)


class HiveSensorEntity(HiveEntity, SensorEntity):
    """Hive Sensor Entity."""

    @property
    def unique_id(self):
        """Return unique ID of entity."""
        return self._unique_id

    @property
    def device_info(self):
        """Return device information."""
        return {
            ATTR_IDENTIFIERS: {(DOMAIN, self.device["device_id"])},
            ATTR_NAME: self.device["device_name"],
            ATTR_MODEL: self.device["deviceData"]["model"],
            ATTR_MANUFACTURER: self.device["deviceData"]["manufacturer"],
            ATTR_SW_VERSION: self.device["deviceData"]["version"],
            "via_device": (DOMAIN, self.device["parentDevice"]),
        }

    @property
    def available(self):
        """Return if sensor is available."""
        return self.device.get("deviceData", {}).get("online")

    @property
    def device_class(self):
        """Device class of the entity."""
        return DEVICETYPE[self.device["hiveType"]].get("type")

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return DEVICETYPE[self.device["hiveType"]].get("unit")

    @property
    def name(self):
        """Return the name of the sensor."""
        return self.device["haName"]

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.device["status"]["state"]

    async def async_update(self):
        """Update all Node data from Hive."""
        await self.hive.session.updateData(self.device)
        self.device = await self.hive.sensor.getSensor(self.device)

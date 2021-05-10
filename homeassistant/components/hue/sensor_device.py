"""Support for the Philips Hue sensor devices."""
from homeassistant.const import (
    ATTR_IDENTIFIERS,
    ATTR_MANUFACTURER,
    ATTR_MODEL,
    ATTR_NAME,
    ATTR_SW_VERSION,
)

from .const import DOMAIN as HUE_DOMAIN


class GenericHueDevice:
    """Representation of a Hue device."""

    def __init__(self, sensor, name, bridge, primary_sensor=None):
        """Initialize the sensor."""
        self.sensor = sensor
        self._name = name
        self._primary_sensor = primary_sensor
        self.bridge = bridge

    @property
    def primary_sensor(self):
        """Return the primary sensor entity of the physical device."""
        return self._primary_sensor or self.sensor

    @property
    def device_id(self):
        """Return the ID of the physical device this sensor is part of."""
        return self.unique_id[:23]

    @property
    def unique_id(self):
        """Return the ID of this Hue sensor."""
        return self.sensor.uniqueid

    @property
    def name(self):
        """Return a friendly name for the sensor."""
        return self._name

    @property
    def swupdatestate(self):
        """Return detail of available software updates for this device."""
        return self.primary_sensor.raw.get("swupdate", {}).get("state")

    @property
    def device_info(self):
        """Return the device info.

        Links individual entities together in the hass device registry.
        """
        return {
            ATTR_IDENTIFIERS: {(HUE_DOMAIN, self.device_id)},
            ATTR_NAME: self.primary_sensor.name,
            ATTR_MANUFACTURER: self.primary_sensor.manufacturername,
            ATTR_MODEL: (
                self.primary_sensor.productname or self.primary_sensor.modelid
            ),
            ATTR_SW_VERSION: self.primary_sensor.swversion,
            "via_device": (HUE_DOMAIN, self.bridge.api.config.bridgeid),
        }

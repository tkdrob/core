"""Support for Fibaro sensors."""
from contextlib import suppress

from homeassistant.components.sensor import DOMAIN, SensorEntity
from homeassistant.const import (
    CONCENTRATION_PARTS_PER_MILLION,
    DEVICE_CLASS_CO2,
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_ILLUMINANCE,
    DEVICE_CLASS_TEMPERATURE,
    LIGHT_LUX,
    PERCENTAGE,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
)

from . import FIBARO_DEVICES, FibaroDevice

SENSOR_TYPES = {
    "com.fibaro.temperatureSensor": [
        "Temperature",
        None,
        None,
        DEVICE_CLASS_TEMPERATURE,
    ],
    "com.fibaro.smokeSensor": [
        "Smoke",
        CONCENTRATION_PARTS_PER_MILLION,
        "mdi:fire",
        None,
    ],
    "CO2": [
        "CO2",
        CONCENTRATION_PARTS_PER_MILLION,
        None,
        None,
        DEVICE_CLASS_CO2,
    ],
    "com.fibaro.humiditySensor": [
        "Humidity",
        PERCENTAGE,
        None,
        DEVICE_CLASS_HUMIDITY,
    ],
    "com.fibaro.lightSensor": ["Light", LIGHT_LUX, None, DEVICE_CLASS_ILLUMINANCE],
}


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Fibaro controller devices."""
    if discovery_info is None:
        return

    add_entities(
        [FibaroSensor(device) for device in hass.data[FIBARO_DEVICES]["sensor"]], True
    )


class FibaroSensor(FibaroDevice, SensorEntity):
    """Representation of a Fibaro Sensor."""

    def __init__(self, fibaro_device):
        """Initialize the sensor."""
        super().__init__(fibaro_device)
        self.entity_id = f"{DOMAIN}.{self.ha_id}"
        if fibaro_device.type in SENSOR_TYPES:
            self._attr_unit_of_measurement = SENSOR_TYPES[fibaro_device.type][1]
            self._attr_icon = SENSOR_TYPES[fibaro_device.type][2]
            self._attr_device_class = SENSOR_TYPES[fibaro_device.type][3]
        with suppress(KeyError, ValueError):
            if not self.unit_of_measurement:
                if self.fibaro_device.properties.unit == "lux":
                    self._attr_unit_of_measurement = LIGHT_LUX
                elif self.fibaro_device.properties.unit == "C":
                    self._attr_unit_of_measurement = TEMP_CELSIUS
                elif self.fibaro_device.properties.unit == "F":
                    self._attr_unit_of_measurement = TEMP_FAHRENHEIT
                else:
                    self._attr_unit_of_measurement = self.fibaro_device.properties.unit

    def update(self):
        """Update the state."""
        with suppress(KeyError, ValueError):
            self._attr_state = float(self.fibaro_device.properties.value)

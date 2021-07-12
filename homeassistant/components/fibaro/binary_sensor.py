"""Support for Fibaro binary sensors."""
from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_DOOR,
    DEVICE_CLASS_MOTION,
    DEVICE_CLASS_SMOKE,
    DEVICE_CLASS_WINDOW,
    DOMAIN,
    BinarySensorEntity,
)
from homeassistant.const import CONF_DEVICE_CLASS, CONF_ICON

from . import FIBARO_DEVICES, FibaroDevice

SENSOR_TYPES = {
    "com.fibaro.floodSensor": ["Flood", "mdi:water", "flood"],
    "com.fibaro.motionSensor": ["Motion", "mdi:run", DEVICE_CLASS_MOTION],
    "com.fibaro.doorSensor": ["Door", "mdi:window-open", DEVICE_CLASS_DOOR],
    "com.fibaro.windowSensor": ["Window", "mdi:window-open", DEVICE_CLASS_WINDOW],
    "com.fibaro.smokeSensor": ["Smoke", "mdi:smoking", DEVICE_CLASS_SMOKE],
    "com.fibaro.FGMS001": ["Motion", "mdi:run", DEVICE_CLASS_MOTION],
    "com.fibaro.heatDetector": ["Heat", "mdi:fire", "heat"],
}


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Perform the setup for Fibaro controller devices."""
    if discovery_info is None:
        return

    add_entities(
        [
            FibaroBinarySensor(device)
            for device in hass.data[FIBARO_DEVICES]["binary_sensor"]
        ],
        True,
    )


class FibaroBinarySensor(FibaroDevice, BinarySensorEntity):
    """Representation of a Fibaro Binary Sensor."""

    def __init__(self, fibaro_device):
        """Initialize the binary_sensor."""
        super().__init__(fibaro_device)
        self.entity_id = f"{DOMAIN}.{self.ha_id}"
        stype = None
        devconf = fibaro_device.device_config
        if fibaro_device.type in SENSOR_TYPES:
            stype = fibaro_device.type
        elif fibaro_device.baseType in SENSOR_TYPES:
            stype = fibaro_device.baseType
        if stype:
            self._attr_device_class = SENSOR_TYPES[stype][2]
            self._attr_icon = SENSOR_TYPES[stype][1]
        # device_config overrides:
        self._attr_device_class = devconf.get(CONF_DEVICE_CLASS, self.device_class)
        self._attr_icon = devconf.get(CONF_ICON, self.icon)

    def update(self):
        """Get the latest data and update the state."""
        self._attr_is_on = self.current_binary_state

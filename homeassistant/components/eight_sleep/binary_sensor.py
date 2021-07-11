"""Support for Eight Sleep binary sensors."""
import logging

from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_OCCUPANCY,
    BinarySensorEntity,
)

from . import CONF_BINARY_SENSORS, DATA_EIGHT, NAME_MAP, EightSleepHeatEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the eight sleep binary sensor."""
    if discovery_info is None:
        return

    name = "Eight"
    sensors = discovery_info[CONF_BINARY_SENSORS]
    eight = hass.data[DATA_EIGHT]

    all_sensors = []

    for sensor in sensors:
        all_sensors.append(EightHeatSensor(name, eight, sensor))

    async_add_entities(all_sensors, True)


class EightHeatSensor(EightSleepHeatEntity, BinarySensorEntity):
    """Representation of a Eight Sleep heat-based sensor."""

    _attr_device_class = DEVICE_CLASS_OCCUPANCY

    def __init__(self, name, eight, sensor):
        """Initialize the sensor."""
        side = sensor.split("_")[0]
        userid = eight.fetch_userid(side)
        self._usrobj = eight.users[userid]

        self._attr_name = f"{name} {NAME_MAP.get(sensor, sensor)}"

        _LOGGER.debug(
            "Presence Sensor: %s, Side: %s, User: %s",
            sensor,
            side,
            userid,
        )

    async def async_update(self):
        """Retrieve latest state."""
        self._attr_state = self._usrobj.bed_presence

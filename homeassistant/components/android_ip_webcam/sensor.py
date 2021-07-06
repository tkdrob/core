"""Support for Android IP Webcam sensors."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.icon import icon_for_battery_level

from . import (
    CONF_HOST,
    CONF_NAME,
    CONF_SENSORS,
    DATA_IP_WEBCAM,
    ICON_MAP,
    KEY_MAP,
    AndroidIPCamEntity,
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the IP Webcam Sensor."""
    if discovery_info is None:
        return

    host = discovery_info[CONF_HOST]
    name = discovery_info[CONF_NAME]
    sensors = discovery_info[CONF_SENSORS]
    ipcam = hass.data[DATA_IP_WEBCAM][host]

    all_sensors = []

    for sensor in sensors:
        all_sensors.append(IPWebcamSensor(name, host, ipcam, sensor))

    async_add_entities(all_sensors, True)


class IPWebcamSensor(AndroidIPCamEntity, SensorEntity):
    """Representation of a IP Webcam sensor."""

    def __init__(self, name, host, ipcam, sensor):
        """Initialize the sensor."""
        super().__init__(host, ipcam)

        self._sensor = sensor
        self._attr_name = f"{name} {KEY_MAP.get(sensor, sensor)}"

    async def async_update(self):
        """Retrieve latest state."""
        if self._sensor in ("audio_connections", "video_connections"):
            if not self._ipcam.status_data:
                return
            self._attr_state = self._ipcam.status_data.get(self._sensor)
            self._attr_unit = "Connections"
        else:
            self._attr_state, self._attr_unit = self._ipcam.export_sensor(self._sensor)
        if self._sensor == "battery_level" and self._state is not None:
            self._attr_icon = icon_for_battery_level(int(self._state))
        else:
            self._attr_icon = ICON_MAP.get(self._sensor, "mdi:eye")

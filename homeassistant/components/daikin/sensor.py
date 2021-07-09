"""Support for Daikin AC sensors."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import (
    CONF_DEVICE_CLASS,
    CONF_ICON,
    CONF_NAME,
    CONF_TYPE,
    CONF_UNIT_OF_MEASUREMENT,
)

from . import DOMAIN as DAIKIN_DOMAIN, DaikinApi
from .const import (
    ATTR_COMPRESSOR_FREQUENCY,
    ATTR_COOL_ENERGY,
    ATTR_HEAT_ENERGY,
    ATTR_HUMIDITY,
    ATTR_INSIDE_TEMPERATURE,
    ATTR_OUTSIDE_TEMPERATURE,
    ATTR_TARGET_HUMIDITY,
    ATTR_TOTAL_POWER,
    SENSOR_TYPE_ENERGY,
    SENSOR_TYPE_FREQUENCY,
    SENSOR_TYPE_HUMIDITY,
    SENSOR_TYPE_POWER,
    SENSOR_TYPE_TEMPERATURE,
    SENSOR_TYPES,
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Old way of setting up the Daikin sensors.

    Can only be called when a user accidentally mentions the platform in their
    config. But even in that case it would have been ignored.
    """


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Daikin climate based on config_entry."""
    daikin_api = hass.data[DAIKIN_DOMAIN].get(entry.entry_id)
    sensors = [ATTR_INSIDE_TEMPERATURE]
    if daikin_api.device.support_outside_temperature:
        sensors.append(ATTR_OUTSIDE_TEMPERATURE)
    if daikin_api.device.support_energy_consumption:
        sensors.append(ATTR_TOTAL_POWER)
        sensors.append(ATTR_COOL_ENERGY)
        sensors.append(ATTR_HEAT_ENERGY)
    if daikin_api.device.support_humidity:
        sensors.append(ATTR_HUMIDITY)
        sensors.append(ATTR_TARGET_HUMIDITY)
    if daikin_api.device.support_compressor_frequency:
        sensors.append(ATTR_COMPRESSOR_FREQUENCY)
    async_add_entities([DaikinSensor.factory(daikin_api, sensor) for sensor in sensors])


class DaikinSensor(SensorEntity):
    """Representation of a Sensor."""

    @staticmethod
    def factory(api: DaikinApi, monitored_state: str):
        """Initialize any DaikinSensor."""
        cls = {
            SENSOR_TYPE_TEMPERATURE: DaikinClimateSensor,
            SENSOR_TYPE_HUMIDITY: DaikinClimateSensor,
            SENSOR_TYPE_POWER: DaikinPowerSensor,
            SENSOR_TYPE_ENERGY: DaikinPowerSensor,
            SENSOR_TYPE_FREQUENCY: DaikinClimateSensor,
        }[SENSOR_TYPES[monitored_state][CONF_TYPE]]
        return cls(api, monitored_state)

    def __init__(self, api: DaikinApi, monitored_state: str) -> None:
        """Initialize the sensor."""
        self._api = api
        self._attr_name = f"{api.name} {SENSOR_TYPES[monitored_state][CONF_NAME]}"
        self._device_attribute = monitored_state
        self._attr_unique_id = f"{api.device.mac}-{monitored_state}"
        self._attr_device_class = SENSOR_TYPES[monitored_state].get(CONF_DEVICE_CLASS)
        self._attr_icon = SENSOR_TYPES[monitored_state].get(CONF_ICON)
        self._attr_unit_of_measurement = SENSOR_TYPES[monitored_state][
            CONF_UNIT_OF_MEASUREMENT
        ]
        self._attr_device_info = api.device_info

    @property
    def state(self):
        """Return the state of the sensor."""
        raise NotImplementedError

    async def async_update(self):
        """Retrieve latest state."""
        await self._api.async_update()


class DaikinClimateSensor(DaikinSensor):
    """Representation of a Climate Sensor."""

    @property
    def state(self):
        """Return the internal state of the sensor."""
        if self._device_attribute == ATTR_INSIDE_TEMPERATURE:
            return self._api.device.inside_temperature
        if self._device_attribute == ATTR_OUTSIDE_TEMPERATURE:
            return self._api.device.outside_temperature

        if self._device_attribute == ATTR_HUMIDITY:
            return self._api.device.humidity
        if self._device_attribute == ATTR_TARGET_HUMIDITY:
            return self._api.device.target_humidity

        if self._device_attribute == ATTR_COMPRESSOR_FREQUENCY:
            return self._api.device.compressor_frequency

        return None


class DaikinPowerSensor(DaikinSensor):
    """Representation of a power/energy consumption sensor."""

    @property
    def state(self):
        """Return the state of the sensor."""
        if self._device_attribute == ATTR_TOTAL_POWER:
            return round(self._api.device.current_total_power_consumption, 2)
        if self._device_attribute == ATTR_COOL_ENERGY:
            return round(self._api.device.last_hour_cool_energy_consumption, 2)
        if self._device_attribute == ATTR_HEAT_ENERGY:
            return round(self._api.device.last_hour_heat_energy_consumption, 2)
        return None

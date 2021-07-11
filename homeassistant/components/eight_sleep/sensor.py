"""Support for Eight Sleep sensors."""
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import PERCENTAGE, TEMP_CELSIUS, TEMP_FAHRENHEIT

from . import (
    CONF_SENSORS,
    DATA_EIGHT,
    NAME_MAP,
    EightSleepHeatEntity,
    EightSleepUserEntity,
)

ATTR_ROOM_TEMP = "Room Temperature"
ATTR_AVG_ROOM_TEMP = "Average Room Temperature"
ATTR_BED_TEMP = "Bed Temperature"
ATTR_AVG_BED_TEMP = "Average Bed Temperature"
ATTR_RESP_RATE = "Respiratory Rate"
ATTR_AVG_RESP_RATE = "Average Respiratory Rate"
ATTR_HEART_RATE = "Heart Rate"
ATTR_AVG_HEART_RATE = "Average Heart Rate"
ATTR_SLEEP_DUR = "Time Slept"
ATTR_LIGHT_PERC = f"Light Sleep {PERCENTAGE}"
ATTR_DEEP_PERC = f"Deep Sleep {PERCENTAGE}"
ATTR_REM_PERC = f"REM Sleep {PERCENTAGE}"
ATTR_TNT = "Tosses & Turns"
ATTR_SLEEP_STAGE = "Sleep Stage"
ATTR_TARGET_HEAT = "Target Heating Level"
ATTR_ACTIVE_HEAT = "Heating Active"
ATTR_DURATION_HEAT = "Heating Time Remaining"
ATTR_PROCESSING = "Processing"
ATTR_SESSION_START = "Session Start"
ATTR_FIT_DATE = "Fitness Date"
ATTR_FIT_DURATION_SCORE = "Fitness Duration Score"
ATTR_FIT_ASLEEP_SCORE = "Fitness Asleep Score"
ATTR_FIT_OUT_SCORE = "Fitness Out-of-Bed Score"
ATTR_FIT_WAKEUP_SCORE = "Fitness Wakeup Score"

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the eight sleep sensors."""
    if discovery_info is None:
        return

    name = "Eight"
    sensors = discovery_info[CONF_SENSORS]
    eight = hass.data[DATA_EIGHT]

    if hass.config.units.is_metric:
        units = "si"
    else:
        units = "us"

    all_sensors = []

    for sensor in sensors:
        if "bed_state" in sensor:
            all_sensors.append(EightHeatSensor(name, eight, sensor))
        elif "room_temp" in sensor:
            all_sensors.append(EightRoomSensor(name, eight, sensor, units))
        else:
            all_sensors.append(EightUserSensor(name, eight, sensor, units))

    async_add_entities(all_sensors, True)


class EightHeatSensor(EightSleepHeatEntity, SensorEntity):
    """Representation of an eight sleep heat-based sensor."""

    _attr_unit_of_measurement = PERCENTAGE

    def __init__(self, name, eight, sensor):
        """Initialize the sensor."""
        super().__init__(eight)

        self._sensor = sensor
        self._attr_name = f"{name} {NAME_MAP.get(sensor, sensor)}"

        side = sensor.split("_")[0]
        userid = eight.fetch_userid(side)
        self._usrobj = eight.users[userid]

        _LOGGER.debug(
            "Heat Sensor: %s, Side: %s, User: %s",
            sensor,
            side,
            userid,
        )

    async def async_update(self):
        """Retrieve latest state."""
        _LOGGER.debug("Updating Heat sensor: %s", self._sensor)
        self._attr_state = self._usrobj.heating_level
        self._attr_extra_state_attributes = {
            ATTR_TARGET_HEAT: self._usrobj.target_heating_level,
            ATTR_ACTIVE_HEAT: self._usrobj.now_heating,
            ATTR_DURATION_HEAT: self._usrobj.heating_remaining,
        }


class EightUserSensor(EightSleepUserEntity, SensorEntity):
    """Representation of an eight sleep user-based sensor."""

    def __init__(self, name, eight, sensor, units):
        """Initialize the sensor."""
        super().__init__(eight)

        self._sensor = sensor
        self._sensor_root = sensor.split("_", 1)[1]
        self._attr_name = f"{name} {NAME_MAP.get(sensor, sensor)}"
        if "bed_temp" in sensor:
            self._attr_icon = "mdi:thermometer"
        if (
            "current_sleep" in sensor
            or "last_sleep" in sensor
            or "current_sleep_fitness" in sensor
        ):
            self._attr_unit_of_measurement = "Score"
        elif "bed_temp" in sensor:
            self._attr_unit_of_measurement = TEMP_FAHRENHEIT
            if units == "si":
                self._attr_unit_of_measurement = TEMP_CELSIUS
        else:
            self._attr_unit_of_measurement = None
        self._attr = None
        self._units = units

        side = sensor.split("_", 1)[0]
        userid = eight.fetch_userid(side)
        self._usrobj = eight.users[userid]

        _LOGGER.debug(
            "User Sensor: %s, Side: %s, User: %s",
            sensor,
            side,
            userid,
        )

    async def async_update(self):
        """Retrieve latest state."""
        _LOGGER.debug("Updating User sensor: %s", self._sensor)
        if "current" in self._sensor:
            if "fitness" in self._sensor:
                self._attr_state = self._usrobj.current_sleep_fitness_score
                self._attr = self._usrobj.current_fitness_values
            else:
                self._attr_state = self._usrobj.current_sleep_score
                self._attr = self._usrobj.current_values
        elif "last" in self._sensor:
            self._attr_state = self._usrobj.last_sleep_score
            self._attr = self._usrobj.last_values
        elif "bed_temp" in self._sensor:
            temp = self._usrobj.current_values["bed_temp"]
            try:
                if self._units == "si":
                    self._attr_state = round(temp, 2)
                else:
                    self._attr_state = round((temp * 1.8) + 32, 2)
            except TypeError:
                self._attr_state = None
        elif "sleep_stage" in self._sensor:
            self._attr_state = self._usrobj.current_values["stage"]
        self.update_attributes()

    def update_attributes(self):
        """Return device state attributes."""
        if self._attr is None:
            # Skip attributes if sensor type doesn't support
            self._attr_extra_state_attributes = None

        elif "fitness" in self._sensor_root:
            state_attr = {
                ATTR_FIT_DATE: self._attr["date"],
                ATTR_FIT_DURATION_SCORE: self._attr["duration"],
                ATTR_FIT_ASLEEP_SCORE: self._attr["asleep"],
                ATTR_FIT_OUT_SCORE: self._attr["out"],
                ATTR_FIT_WAKEUP_SCORE: self._attr["wakeup"],
            }
            self._attr_extra_state_attributes = state_attr
        else:
            state_attr = {ATTR_SESSION_START: self._attr["date"]}
            state_attr[ATTR_TNT] = self._attr["tnt"]
            state_attr[ATTR_PROCESSING] = self._attr["processing"]

            sleep_time = (
                sum(self._attr["breakdown"].values()) - self._attr["breakdown"]["awake"]
            )
            state_attr[ATTR_SLEEP_DUR] = sleep_time
            try:
                state_attr[ATTR_LIGHT_PERC] = round(
                    (self._attr["breakdown"]["light"] / sleep_time) * 100, 2
                )
            except ZeroDivisionError:
                state_attr[ATTR_LIGHT_PERC] = 0
            try:
                state_attr[ATTR_DEEP_PERC] = round(
                    (self._attr["breakdown"]["deep"] / sleep_time) * 100, 2
                )
            except ZeroDivisionError:
                state_attr[ATTR_DEEP_PERC] = 0

            try:
                state_attr[ATTR_REM_PERC] = round(
                    (self._attr["breakdown"]["rem"] / sleep_time) * 100, 2
                )
            except ZeroDivisionError:
                state_attr[ATTR_REM_PERC] = 0

            try:
                if self._units == "si":
                    room_temp = round(self._attr["room_temp"], 2)
                else:
                    room_temp = round((self._attr["room_temp"] * 1.8) + 32, 2)
            except TypeError:
                room_temp = None

            try:
                if self._units == "si":
                    bed_temp = round(self._attr["bed_temp"], 2)
                else:
                    bed_temp = round((self._attr["bed_temp"] * 1.8) + 32, 2)
            except TypeError:
                bed_temp = None

            if "current" in self._sensor_root:
                try:
                    state_attr[ATTR_RESP_RATE] = round(self._attr["resp_rate"], 2)
                except TypeError:
                    state_attr[ATTR_RESP_RATE] = None
                try:
                    state_attr[ATTR_HEART_RATE] = round(self._attr["heart_rate"], 2)
                except TypeError:
                    state_attr[ATTR_HEART_RATE] = None
                state_attr[ATTR_SLEEP_STAGE] = self._attr["stage"]
                state_attr[ATTR_ROOM_TEMP] = room_temp
                state_attr[ATTR_BED_TEMP] = bed_temp
            elif "last" in self._sensor_root:
                try:
                    state_attr[ATTR_AVG_RESP_RATE] = round(self._attr["resp_rate"], 2)
                except TypeError:
                    state_attr[ATTR_AVG_RESP_RATE] = None
                try:
                    state_attr[ATTR_AVG_HEART_RATE] = round(self._attr["heart_rate"], 2)
                except TypeError:
                    state_attr[ATTR_AVG_HEART_RATE] = None
                state_attr[ATTR_AVG_ROOM_TEMP] = room_temp
                state_attr[ATTR_AVG_BED_TEMP] = bed_temp

            self._attr_extra_state_attributes = state_attr


class EightRoomSensor(EightSleepUserEntity, SensorEntity):
    """Representation of an eight sleep room sensor."""

    _attr_icon = "mdi:thermometer"

    def __init__(self, name, eight, sensor, units):
        """Initialize the sensor."""
        super().__init__(eight)

        self._sensor = sensor
        self._attr_name = f"{name} {NAME_MAP.get(sensor, sensor)}"
        self._attr_unit_of_measurement = TEMP_FAHRENHEIT
        if units == "si":
            self._attr_unit_of_measurement = TEMP_CELSIUS
        self._units = units

    async def async_update(self):
        """Retrieve latest state."""
        _LOGGER.debug("Updating Room sensor: %s", self._sensor)
        temp = self._eight.room_temperature()
        try:
            if self._units == "si":
                self._attr_state = round(temp, 2)
            else:
                self._attr_state = round((temp * 1.8) + 32, 2)
        except TypeError:
            self._attr_state = None

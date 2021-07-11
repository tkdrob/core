"""Support for Ebusd sensors."""
import datetime
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.util import Throttle
import homeassistant.util.dt as dt_util

from .const import DOMAIN

TIME_FRAME1_BEGIN = "time_frame1_begin"
TIME_FRAME1_END = "time_frame1_end"
TIME_FRAME2_BEGIN = "time_frame2_begin"
TIME_FRAME2_END = "time_frame2_end"
TIME_FRAME3_BEGIN = "time_frame3_begin"
TIME_FRAME3_END = "time_frame3_end"
MIN_TIME_BETWEEN_UPDATES = datetime.timedelta(seconds=15)

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Ebus sensor."""
    ebusd_api = hass.data[DOMAIN]
    monitored_conditions = discovery_info["monitored_conditions"]
    name = discovery_info["client_name"]

    dev = []
    for condition in monitored_conditions:
        dev.append(
            EbusdSensor(ebusd_api, discovery_info["sensor_types"][condition], name)
        )

    add_entities(dev, True)


class EbusdSensor(SensorEntity):
    """Ebusd component sensor methods definition."""

    def __init__(self, data, sensor, name):
        """Initialize the sensor."""
        sname, self._attr_unit_of_measurement, self._attr_icon, self._type = sensor
        self._attr_name = f"{name} {sname}"
        self.data = data

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Fetch new state data for the sensor."""
        try:
            self.data.update(self.name, self._type)
            if self.name not in self.data.value:
                return

            self._attr_state = self.data.value[self.name]
        except RuntimeError:
            _LOGGER.debug("EbusdData.update exception")
        if self._type == 1 and self.state is not None:
            schedule = {
                TIME_FRAME1_BEGIN: None,
                TIME_FRAME1_END: None,
                TIME_FRAME2_BEGIN: None,
                TIME_FRAME2_END: None,
                TIME_FRAME3_BEGIN: None,
                TIME_FRAME3_END: None,
            }
            time_frame = self.state.split(";")
            for index, item in enumerate(sorted(schedule.items())):
                if index < len(time_frame):
                    parsed = datetime.datetime.strptime(time_frame[index], "%H:%M")
                    parsed = parsed.replace(
                        dt_util.now().year, dt_util.now().month, dt_util.now().day
                    )
                    schedule[item[0]] = parsed.isoformat()
            self._attr_extra_state_attributes = schedule
        else:
            self._attr_extra_state_attributes = None

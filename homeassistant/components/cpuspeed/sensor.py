"""Support for displaying the current CPU speed."""
from cpuinfo import cpuinfo
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import CONF_NAME, FREQUENCY_GIGAHERTZ
import homeassistant.helpers.config_validation as cv

ATTR_BRAND = "brand"
ATTR_HZ = "ghz_advertised"
ATTR_ARCH = "arch"

HZ_ACTUAL = "hz_actual"
HZ_ADVERTISED = "hz_advertised"

DEFAULT_NAME = "CPU speed"

ICON = "mdi:pulse"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string}
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the CPU speed sensor."""
    name = config[CONF_NAME]
    add_entities([CpuSpeedSensor(name)], True)


class CpuSpeedSensor(SensorEntity):
    """Representation of a CPU sensor."""

    _attr_icon = ICON
    _attr_unit_of_measurement = FREQUENCY_GIGAHERTZ

    def __init__(self, name):
        """Initialize the CPU sensor."""
        self._attr_name = name

    def update(self):
        """Get the latest data and updates the state."""
        info = cpuinfo.get_cpu_info()
        if HZ_ACTUAL in info:
            self._attr_state = round(float(info[HZ_ACTUAL][0]) / 10 ** 9, 2)
        else:
            self._attr_state = None
        if info is not None:
            attrs = {
                ATTR_ARCH: info["arch_string_raw"],
                ATTR_BRAND: info["brand_raw"],
            }
            if HZ_ADVERTISED in info:
                attrs[ATTR_HZ] = round(info[HZ_ADVERTISED][0] / 10 ** 9, 2)
            self._attr_extra_state_attributes = attrs

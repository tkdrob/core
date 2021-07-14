"""Support for switches using GC100."""
import voluptuous as vol

from homeassistant.components.switch import PLATFORM_SCHEMA
from homeassistant.const import DEVICE_DEFAULT_NAME
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import ToggleEntity

from . import CONF_PORTS, DATA_GC100

_SWITCH_SCHEMA = vol.Schema({cv.string: cv.string})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {vol.Required(CONF_PORTS): vol.All(cv.ensure_list, [_SWITCH_SCHEMA])}
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the GC100 devices."""
    switches = []
    ports = config.get(CONF_PORTS)
    for port in ports:
        for port_addr, port_name in port.items():
            switches.append(GC100Switch(port_name, port_addr, hass.data[DATA_GC100]))
    add_entities(switches, True)


class GC100Switch(ToggleEntity):
    """Represent a switch/relay from GC100."""

    def __init__(self, name, port_addr, gc100):
        """Initialize the GC100 switch."""
        self._attr_name = name or DEVICE_DEFAULT_NAME
        self._port_addr = port_addr
        self._gc100 = gc100

    def turn_on(self, **kwargs):
        """Turn the device on."""
        self._gc100.write_switch(self._port_addr, 1, self.set_state)

    def turn_off(self, **kwargs):
        """Turn the device off."""
        self._gc100.write_switch(self._port_addr, 0, self.set_state)

    def update(self):
        """Update the sensor state."""
        self._gc100.read_sensor(self._port_addr, self.set_state)

    def set_state(self, state):
        """Set the current state."""
        self._attr_is_on = state == 1
        self.schedule_update_ha_state()

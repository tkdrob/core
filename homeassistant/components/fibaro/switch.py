"""Support for Fibaro switches."""
from homeassistant.components.switch import DOMAIN, SwitchEntity
from homeassistant.util import convert

from . import FIBARO_DEVICES, FibaroDevice


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Fibaro switches."""
    if discovery_info is None:
        return

    add_entities(
        [FibaroSwitch(device) for device in hass.data[FIBARO_DEVICES]["switch"]], True
    )


class FibaroSwitch(FibaroDevice, SwitchEntity):
    """Representation of a Fibaro Switch."""

    def __init__(self, fibaro_device):
        """Initialize the Fibaro device."""
        super().__init__(fibaro_device)
        self.entity_id = f"{DOMAIN}.{self.ha_id}"

    def turn_on(self, **kwargs):
        """Turn device on."""
        self.call_turn_on()
        self._attr_is_on = True

    def turn_off(self, **kwargs):
        """Turn device off."""
        self.call_turn_off()
        self._attr_is_on = False

    def update(self):
        """Update device state."""
        self._attr_is_on = self.current_binary_state
        self._attr_today_energy_kwh = None
        if "energy" in self.fibaro_device.interfaces:
            self._attr_today_energy_kwh = convert(
                self.fibaro_device.properties.energy, float, 0.0
            )
        self._attr_current_power_w = None
        if "power" in self.fibaro_device.interfaces:
            self._attr_current_power_w = convert(
                self.fibaro_device.properties.power, float, 0.0
            )

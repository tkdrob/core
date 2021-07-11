"""Support for Eufy switches."""
import lakeside

from homeassistant.components.switch import SwitchEntity


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up Eufy switches."""
    if discovery_info is None:
        return
    add_entities([EufySwitch(discovery_info)], True)


class EufySwitch(SwitchEntity):
    """Representation of a Eufy switch."""

    def __init__(self, device):
        """Initialize the light."""

        self._attr_name = device["name"]
        self._attr_unique_id = device["address"]
        self._switch = lakeside.switch(
            device["address"], device["code"], device["type"]
        )
        self._switch.connect()

    def update(self):
        """Synchronise state from the switch."""
        self._switch.update()
        self._attr_is_on = self._switch.power

    def turn_on(self, **kwargs):
        """Turn the specified switch on."""
        try:
            self._switch.set_state(True)
        except BrokenPipeError:
            self._switch.connect()
            self._switch.set_state(power=True)

    def turn_off(self, **kwargs):
        """Turn the specified switch off."""
        try:
            self._switch.set_state(False)
        except BrokenPipeError:
            self._switch.connect()
            self._switch.set_state(False)

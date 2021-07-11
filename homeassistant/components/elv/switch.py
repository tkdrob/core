"""Support for PCA 301 smart switch."""
import logging

import pypca
from serial import SerialException

from homeassistant.components.switch import ATTR_CURRENT_POWER_W, SwitchEntity
from homeassistant.const import EVENT_HOMEASSISTANT_STOP

_LOGGER = logging.getLogger(__name__)

ATTR_TOTAL_ENERGY_KWH = "total_energy_kwh"

DEFAULT_NAME = "PCA 301"


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the PCA switch platform."""

    if discovery_info is None:
        return

    serial_device = discovery_info["device"]

    try:
        pca = pypca.PCA(serial_device)
        pca.open()

        entities = [SmartPlugSwitch(pca, device) for device in pca.get_devices()]
        add_entities(entities, True)

    except SerialException as exc:
        _LOGGER.warning("Unable to open serial port: %s", exc)
        return

    hass.bus.listen_once(EVENT_HOMEASSISTANT_STOP, pca.close)

    pca.start_scan()


class SmartPlugSwitch(SwitchEntity):
    """Representation of a PCA Smart Plug switch."""

    def __init__(self, pca, device_id):
        """Initialize the switch."""
        self._device_id = device_id
        self._attr_name = "PCA 301"
        self._attr_extra_state_attributes = {}
        self._pca = pca

    def turn_on(self, **kwargs):
        """Turn the switch on."""
        self._pca.turn_on(self._device_id)

    def turn_off(self, **kwargs):
        """Turn the switch off."""
        self._pca.turn_off(self._device_id)

    def update(self):
        """Update the PCA switch's state."""
        try:
            self._attr_extra_state_attributes[
                ATTR_CURRENT_POWER_W
            ] = f"{self._pca.get_current_power(self._device_id):.1f}"
            self._attr_extra_state_attributes[
                ATTR_TOTAL_ENERGY_KWH
            ] = f"{self._pca.get_total_consumption(self._device_id):.2f}"

            self._attr_available = True
            self._attr_is_on = self._pca.get_state(self._device_id)

        except (OSError) as ex:
            if self.available:
                _LOGGER.warning("Could not read state for %s: %s", self.name, ex)
                self._attr_available = False

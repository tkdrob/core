"""Platform for Flexit AC units with CI66 Modbus adapter."""
from __future__ import annotations

import logging

from pyflexit.pyflexit import pyflexit
import voluptuous as vol

from homeassistant.components.climate import PLATFORM_SCHEMA, ClimateEntity
from homeassistant.components.climate.const import (
    HVAC_MODE_COOL,
    SUPPORT_FAN_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.components.modbus.const import CONF_HUB, DEFAULT_HUB, MODBUS_DOMAIN
from homeassistant.const import (
    ATTR_TEMPERATURE,
    CONF_NAME,
    CONF_SLAVE,
    DEVICE_DEFAULT_NAME,
    TEMP_CELSIUS,
)
import homeassistant.helpers.config_validation as cv

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_HUB, default=DEFAULT_HUB): cv.string,
        vol.Required(CONF_SLAVE): vol.All(int, vol.Range(min=0, max=32)),
        vol.Optional(CONF_NAME, default=DEVICE_DEFAULT_NAME): cv.string,
    }
)

_LOGGER = logging.getLogger(__name__)

SUPPORT_FLAGS = SUPPORT_TARGET_TEMPERATURE | SUPPORT_FAN_MODE


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Flexit Platform."""
    modbus_slave = config.get(CONF_SLAVE)
    name = config.get(CONF_NAME)
    hub = hass.data[MODBUS_DOMAIN][config.get(CONF_HUB)]
    add_entities([Flexit(hub, modbus_slave, name)], True)


class Flexit(ClimateEntity):
    """Representation of a Flexit AC unit."""

    _attr_fan_modes = ["Off", "Low", "Medium", "High"]
    _attr_hvac_modes = [HVAC_MODE_COOL]
    _attr_should_poll = True
    _attr_supported_features = SUPPORT_FLAGS
    _attr_temperature_unit = TEMP_CELSIUS

    def __init__(self, hub, modbus_slave, name):
        """Initialize the unit."""
        self._attr_name = name
        self.unit = pyflexit(hub, modbus_slave)

    def update(self):
        """Update unit attributes."""
        if not self.unit.update():
            _LOGGER.warning("Modbus read failed")

        self._attr_target_temperature = self.unit.get_target_temp
        self._attr_current_temperature = self.unit.get_temp
        self._attr_fan_mode = self.fan_modes[self.unit.get_fan_speed]
        # Current operation mode
        self._attr_hvac_mode = self.unit.get_operation
        self._attr_extra_state_attributes = {
            "filter_hours": self.unit.get_filter_hours,
            "filter_alarm": self.unit.get_filter_alarm,
            "heat_recovery": self.unit.get_heat_recovery,
            "heating": self.unit.get_heating,
            "heater_enabled": self.unit.get_heater_enabled,
            "cooling": self.unit.get_cooling,
        }

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        if kwargs.get(ATTR_TEMPERATURE) is not None:
            self._attr_target_temperature = kwargs.get(ATTR_TEMPERATURE)
        self.unit.set_temp(self.target_temperature)

    def set_fan_mode(self, fan_mode):
        """Set new fan mode."""
        self.unit.set_fan_speed(self.fan_modes.index(fan_mode))

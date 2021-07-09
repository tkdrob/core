"""Support for currencylayer.com exchange rates service."""
from datetime import timedelta
import logging

import requests
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import (
    ATTR_ATTRIBUTION,
    CONF_API_KEY,
    CONF_BASE,
    CONF_NAME,
    CONF_QUOTE,
)
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)
_RESOURCE = "http://apilayer.net/api/live"

ATTRIBUTION = "Data provided by currencylayer.com"

DEFAULT_BASE = "USD"
DEFAULT_NAME = "CurrencyLayer Sensor"

ICON = "mdi:currency"

SCAN_INTERVAL = timedelta(hours=4)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_API_KEY): cv.string,
        vol.Required(CONF_QUOTE): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(CONF_BASE, default=DEFAULT_BASE): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Currencylayer sensor."""
    base = config[CONF_BASE]
    api_key = config[CONF_API_KEY]
    parameters = {"source": base, "access_key": api_key, "format": 1}

    rest = CurrencylayerData(_RESOURCE, parameters)

    response = requests.get(_RESOURCE, params=parameters, timeout=10)
    sensors = []
    for variable in config[CONF_QUOTE]:
        sensors.append(CurrencylayerSensor(rest, base, variable))
    if "error" in response.json():
        return False
    add_entities(sensors, True)


class CurrencylayerSensor(SensorEntity):
    """Implementing the Currencylayer sensor."""

    _attr_icon = ICON

    def __init__(self, rest, base, quote):
        """Initialize the sensor."""
        self.rest = rest
        self._attr_unit_of_measurement = quote
        self._attr_name = base

    def update(self):
        """Update current date."""
        self.rest.update()
        value = self.rest.data
        if value is not None:
            self._attr_state = round(value[f"{self.name}{self.unit_of_measurement}"], 4)
        self._attr_extra_state_attributes = {ATTR_ATTRIBUTION: ATTRIBUTION}


class CurrencylayerData:
    """Get data from Currencylayer.org."""

    def __init__(self, resource, parameters):
        """Initialize the data object."""
        self._resource = resource
        self._parameters = parameters
        self.data = None

    def update(self):
        """Get the latest data from Currencylayer."""
        try:
            result = requests.get(self._resource, params=self._parameters, timeout=10)
            if "error" in result.json():
                raise ValueError(result.json()["error"]["info"])
            self.data = result.json()["quotes"]
            _LOGGER.debug("Currencylayer data updated: %s", result.json()["timestamp"])
        except ValueError as err:
            _LOGGER.error("Check Currencylayer API %s", err.args)
            self.data = None

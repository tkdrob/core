"""Currency exchange rate support that comes from fixer.io."""
from datetime import timedelta
import logging

from fixerio import Fixerio
from fixerio.exceptions import FixerioException
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import ATTR_ATTRIBUTION, CONF_API_KEY, CONF_NAME, CONF_TARGET
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

ATTR_EXCHANGE_RATE = "Exchange rate"
ATTR_TARGET = "Target currency"
ATTRIBUTION = "Data provided by the European Central Bank (ECB)"

DEFAULT_BASE = "USD"
DEFAULT_NAME = "Exchange rate"

ICON = "mdi:currency-usd"

SCAN_INTERVAL = timedelta(days=1)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_API_KEY): cv.string,
        vol.Required(CONF_TARGET): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Fixer.io sensor."""
    api_key = config.get(CONF_API_KEY)
    name = config.get(CONF_NAME)
    target = config.get(CONF_TARGET)

    try:
        Fixerio(symbols=[target], access_key=api_key).latest()
    except FixerioException:
        _LOGGER.error("One of the given currencies is not supported")
        return

    data = ExchangeData(target, api_key)
    add_entities([ExchangeRateSensor(data, name, target)], True)


class ExchangeRateSensor(SensorEntity):
    """Representation of a Exchange sensor."""

    _attr_icon = ICON

    def __init__(self, data, name, target):
        """Initialize the sensor."""
        self.data = data
        self._attr_unit_of_measurement = target
        self._attr_name = name

    def update(self):
        """Get the latest data and updates the states."""
        self.data.update()
        self._attr_state = round(self.data.rate["rates"][self.unit_of_measurement], 3)
        if self.data.rate is not None:
            self._attr_extra_state_attributes = {
                ATTR_ATTRIBUTION: ATTRIBUTION,
                ATTR_EXCHANGE_RATE: self.data.rate["rates"][self.unit_of_measurement],
                ATTR_TARGET: self.unit_of_measurement,
            }


class ExchangeData:
    """Get the latest data and update the states."""

    def __init__(self, target_currency, api_key):
        """Initialize the data object."""
        self.rate = None
        self.exchange = Fixerio(symbols=[target_currency], access_key=api_key)

    def update(self):
        """Get the latest data from Fixer.io."""
        self.rate = self.exchange.latest()

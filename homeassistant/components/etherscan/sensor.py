"""Support for Etherscan sensors."""
from datetime import timedelta

from pyetherscan import get_balance
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import ATTR_ATTRIBUTION, CONF_ADDRESS, CONF_NAME, CONF_TOKEN
import homeassistant.helpers.config_validation as cv

ATTRIBUTION = "Data provided by etherscan.io"

CONF_TOKEN_ADDRESS = "token_address"

SCAN_INTERVAL = timedelta(minutes=5)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_ADDRESS): cv.string,
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_TOKEN): cv.string,
        vol.Optional(CONF_TOKEN_ADDRESS): cv.string,
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Etherscan.io sensors."""
    address = config.get(CONF_ADDRESS)
    name = config.get(CONF_NAME)
    token = config.get(CONF_TOKEN)
    token_address = config.get(CONF_TOKEN_ADDRESS)

    if token:
        token = token.upper()
        if not name:
            name = "%s Balance" % token
    if not name:
        name = "ETH Balance"

    add_entities([EtherscanSensor(name, address, token, token_address)], True)


class EtherscanSensor(SensorEntity):
    """Representation of an Etherscan.io sensor."""

    def __init__(self, name, address, token, token_address):
        """Initialize the sensor."""
        self._attr_name = name
        self._address = address
        self._token_address = token_address
        self._token = token
        self._attr_unit_of_measurement = self._token or "ETH"

    def update(self):
        """Get the latest state of the sensor."""

        if self._token_address:
            self._attr_state = get_balance(self._address, self._token_address)
        elif self._token:
            self._attr_state = get_balance(self._address, self._token)
        else:
            self._attr_state = get_balance(self._address)
        self._attr_extra_state_attributes = {ATTR_ATTRIBUTION: ATTRIBUTION}

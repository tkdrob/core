"""Support for Epson Workforce Printer."""
from datetime import timedelta

from epsonprinter_pkg.epsonprinterapi import EpsonPrinterAPI
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import CONF_HOST, CONF_MONITORED_CONDITIONS, PERCENTAGE
from homeassistant.exceptions import PlatformNotReady
import homeassistant.helpers.config_validation as cv

MONITORED_CONDITIONS = {
    "black": ["Ink level Black", PERCENTAGE, "mdi:water"],
    "photoblack": ["Ink level Photoblack", PERCENTAGE, "mdi:water"],
    "magenta": ["Ink level Magenta", PERCENTAGE, "mdi:water"],
    "cyan": ["Ink level Cyan", PERCENTAGE, "mdi:water"],
    "yellow": ["Ink level Yellow", PERCENTAGE, "mdi:water"],
    "clean": ["Cleaning level", PERCENTAGE, "mdi:water"],
}
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_MONITORED_CONDITIONS): vol.All(
            cv.ensure_list, [vol.In(MONITORED_CONDITIONS)]
        ),
    }
)
SCAN_INTERVAL = timedelta(minutes=60)


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the cartridge sensor."""
    host = config.get(CONF_HOST)

    api = EpsonPrinterAPI(host)
    if not api.available:
        raise PlatformNotReady()

    sensors = [
        EpsonPrinterCartridge(api, condition)
        for condition in config[CONF_MONITORED_CONDITIONS]
    ]

    add_devices(sensors, True)


class EpsonPrinterCartridge(SensorEntity):
    """Representation of a cartridge sensor."""

    def __init__(self, api, cartridgeidx):
        """Initialize a cartridge sensor."""
        self._api = api

        self._id = cartridgeidx
        self._attr_name = MONITORED_CONDITIONS[self._id][0]
        self._attr_unit_of_measurement = MONITORED_CONDITIONS[self._id][1]
        self._attr_icon = MONITORED_CONDITIONS[self._id][2]

    def update(self):
        """Get the latest data from the Epson printer."""
        self._api.update()
        self._attr_available = self._api.available
        self._attr_state = self._api.getSensorValue(self._id)

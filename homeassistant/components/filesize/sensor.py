"""Sensor for monitoring the size of a file."""
import datetime
import logging
import os

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import DATA_MEGABYTES
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.reload import setup_reload_service

from . import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)


CONF_FILE_PATHS = "file_paths"
ICON = "mdi:file"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {vol.Required(CONF_FILE_PATHS): vol.All(cv.ensure_list, [cv.isfile])}
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the file size sensor."""

    setup_reload_service(hass, DOMAIN, PLATFORMS)

    sensors = []
    for path in config.get(CONF_FILE_PATHS):
        if not hass.config.is_allowed_path(path):
            _LOGGER.error("Filepath %s is not valid or allowed", path)
            continue
        sensors.append(Filesize(path))

    if sensors:
        add_entities(sensors, True)


class Filesize(SensorEntity):
    """Encapsulates file size information."""

    _attr_icon = ICON
    _attr_unit_of_measurement = DATA_MEGABYTES

    def __init__(self, path):
        """Initialize the data object."""
        self._path = path  # Need to check its a valid path
        self._attr_name = path.split("/")[-1]

    def update(self):
        """Update the sensor."""
        statinfo = os.stat(self._path)
        last_updated = datetime.datetime.fromtimestamp(statinfo.st_mtime)
        self._attr_state = round(statinfo.st_size / 1e6, 2)
        self._attr_extra_state_attributes = {
            "path": self._path,
            "last_updated": last_updated.isoformat(),
            "bytes": statinfo.st_size,
        }

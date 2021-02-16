"""Support for the Skybell HD Doorbell."""
from logging import getLogger

from requests.exceptions import ConnectTimeout, HTTPError
from skybellpy import Skybell

from homeassistant.components.binary_sensor import DOMAIN as DOMAIN_BINARY_SENSOR
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ATTRIBUTION,
    CONF_PASSWORD,
    CONF_USERNAME,
    __version__,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import Entity

_LOGGER = getLogger(__name__)

PLATFORMS = [DOMAIN_BINARY_SENSOR]

ATTRIBUTION = "Data provided by Skybell.com"

NOTIFICATION_ID = "skybell_notification"
NOTIFICATION_TITLE = "Skybell Sensor Setup"

DOMAIN = "skybell"
DEFAULT_CACHEDB = "./skybell_cache.pickle"
DEFAULT_ENTITY_NAMESPACE = "skybell"

AGENT_IDENTIFIER = f"HomeAssistant/{__version__}"


async def async_setup(hass: HomeAssistant, config):
    """Set up the Goal Zero Yeti component."""

    hass.data[DOMAIN] = {}

    return True


async def async_setup_entry(hass, entry):
    """Set up Goal Zero Yeti from a config entry."""
    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]

    try:
        cache = hass.config.path(DEFAULT_CACHEDB)
        skybell = Skybell(
            session=async_get_clientsession(hass),
            loop=hass.loop,
            username=username,
            password=password,
            get_devices=True,
            cache_path=cache,
            agent_identifier=AGENT_IDENTIFIER,
        )

        hass.data[DOMAIN] = skybell
    except (ConnectTimeout, HTTPError) as ex:
        _LOGGER.error("Unable to connect to Skybell service: %s", str(ex))
        hass.components.persistent_notification.create(
            "Error: {}<br />"
            "You will need to restart hass after fixing."
            "".format(ex),
            title=NOTIFICATION_TITLE,
            notification_id=NOTIFICATION_ID,
        )
        return False
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    for component in PLATFORMS:
        hass.config_entries.async_forward_entry_unload(entry, component)
    hass.data[DOMAIN].pop(entry.entry_id)


class SkybellDevice(Entity):
    """A HA implementation for Skybell devices."""

    def __init__(self, device):
        """Initialize a sensor for Skybell device."""
        self._device = device

    def update(self):
        """Update automation state."""
        self._device.refresh()

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return {
            ATTR_ATTRIBUTION: ATTRIBUTION,
            "device_id": self._device.device_id,
            "status": self._device.status,
            "location": self._device.location,
            "wifi_ssid": self._device.wifi_ssid,
            "wifi_status": self._device.wifi_status,
            "last_check_in": self._device.last_check_in,
            "motion_threshold": self._device.motion_threshold,
            "video_profile": self._device.video_profile,
        }

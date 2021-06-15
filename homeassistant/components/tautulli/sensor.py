"""A platform which allows you to get information from Tautulli."""
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_API_KEY,
    CONF_HOST,
    CONF_MONITORED_CONDITIONS,
    CONF_NAME,
    CONF_PATH,
    CONF_PORT,
    CONF_SSL,
    CONF_VERIFY_SSL,
)
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv

from . import TautulliEntity
from .const import (
    CONF_MONITORED_USERS,
    DATA_KEY_API,
    DATA_KEY_COORDINATOR,
    DEFAULT_NAME,
    DEFAULT_PATH,
    DEFAULT_PORT,
    DEFAULT_SSL,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
)

PLATFORM_SCHEMA = cv.deprecated(
    vol.All(
        PLATFORM_SCHEMA.extend(
            {
                vol.Required(CONF_API_KEY): cv.string,
                vol.Required(CONF_HOST): cv.string,
                vol.Optional(CONF_MONITORED_CONDITIONS): vol.All(
                    cv.ensure_list, [cv.string]
                ),
                vol.Optional(CONF_MONITORED_USERS): vol.All(
                    cv.ensure_list, [cv.string]
                ),
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.string,
                vol.Optional(CONF_PATH, default=DEFAULT_PATH): cv.string,
                vol.Optional(CONF_SSL, default=DEFAULT_SSL): cv.boolean,
                vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): cv.boolean,
            }
        )
    )
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Set up Tautulli sensor."""
    sensor = [
        TautulliSensor(
            hass.data[DOMAIN][entry.entry_id][DATA_KEY_API],
            hass.data[DOMAIN][entry.entry_id][DATA_KEY_COORDINATOR],
            DEFAULT_NAME,
            entry.options[CONF_MONITORED_USERS],
            entry.entry_id,
        )
    ]

    async_add_entities(sensor)


class TautulliSensor(TautulliEntity, SensorEntity):
    """Representation of a Tautulli sensor."""

    def __init__(self, api, coordinator, name, users, server_unique_id):
        """Initialize the Tautulli sensor."""
        super().__init__(api, coordinator, name, server_unique_id)
        self.usernames = users
        self._attributes = {}
        self._name = name
        self.api = api

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.api.session_data.get("stream_count")

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return "mdi:plex"

    @property
    def unit_of_measurement(self):
        """Return the unit this state is expressed in."""
        return "Watching"

    @property
    def unique_id(self):
        """Return the unique id of the sensor."""
        return f"{self._server_unique_id}/{self._name}"

    @property
    def extra_state_attributes(self):
        """Return attributes for the sensor."""
        self._attributes["Top Movie"] = self.api.home_data.get("movie")
        self._attributes["Top TV Show"] = self.api.home_data.get("tv")
        self._attributes["Top User"] = self.api.home_data.get("user")
        for key in self.api.session_data:
            if "sessions" not in key:
                self._attributes[key] = self.api.session_data[key]
        for user in self.usernames:
            if self.usernames is None or user in self.usernames:
                self._attributes[user] = {}
                self._attributes[user]["Activity"] = self.api.tautulli_user_data[user][
                    "Activity"
                ]
        return self._attributes

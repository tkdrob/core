"""Support for displaying details about a Gitter.im chat room."""
import logging

from gitterpy.client import GitterClient
from gitterpy.errors import GitterRoomError, GitterTokenError
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import CONF_API_KEY, CONF_NAME, CONF_ROOM
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

ATTR_MENTION = "mention"
ATTR_ROOM = "room"
ATTR_USERNAME = "username"

DEFAULT_NAME = "Gitter messages"
DEFAULT_ROOM = "home-assistant/home-assistant"

ICON = "mdi:message-cog"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_API_KEY): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_ROOM, default=DEFAULT_ROOM): cv.string,
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Gitter sensor."""

    name = config.get(CONF_NAME)
    api_key = config.get(CONF_API_KEY)
    room = config.get(CONF_ROOM)

    gitter = GitterClient(api_key)
    try:
        username = gitter.auth.get_my_id["name"]
    except GitterTokenError:
        _LOGGER.error("Token is not valid")
        return

    add_entities([GitterSensor(gitter, room, name, username)], True)


class GitterSensor(SensorEntity):
    """Representation of a Gitter sensor."""

    _attr_icon = ICON
    _attr_unit_of_measurement = "Msg"

    def __init__(self, data, room, name, username):
        """Initialize the sensor."""
        self._attr_name = name
        self._data = data
        self._room = room
        self._username = username
        self._mention = 0

    def update(self):
        """Get the latest data and updates the state."""

        try:
            data = self._data.user.unread_items(self._room)
        except GitterRoomError as error:
            _LOGGER.error(error)
            return

        if "error" not in data:
            self._mention = len(data["mention"])
            self._attr_state = len(data["chat"])
        else:
            _LOGGER.error("Not joined: %s", self._room)

        self._attr_extra_state_attributes = {
            ATTR_USERNAME: self._username,
            ATTR_ROOM: self._room,
            ATTR_MENTION: self._mention,
        }

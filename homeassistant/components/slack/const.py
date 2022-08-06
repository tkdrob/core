"""Constants for the Slack integration."""
import logging
from typing import Final

ATTR_BLOCKS = "blocks"
ATTR_BLOCKS_TEMPLATE = "blocks_template"
ATTR_FILE = "file"
ATTR_LAST_ACTIVITY = "last_activity"
ATTR_PASSWORD = "password"
ATTR_PATH = "path"
ATTR_SNOOZE = "snooze_remaining"
ATTR_STATUS_EMOJI = "status_emoji"
ATTR_STATUS_EXPIRATION = "status_expiration"
ATTR_STATUS_TEXT = "status_text"
ATTR_URL = "url"
ATTR_USER_ID = "user_id"
ATTR_USERNAME = "username"

CONF_DEFAULT_CHANNEL = "default_channel"

DATA_CLIENT = "client"
DEFAULT_NAME = "Slack"
DEFAULT_TIMEOUT_SECONDS = 15
DOMAIN: Final = "slack"

LOGGER = logging.getLogger(__package__)

SERVICE_SET_STATUS = "set_status"

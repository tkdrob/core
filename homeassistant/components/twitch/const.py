"""Constants for the Twitch integration."""
from datetime import timedelta

ATTRIBUTION = "Data provided by Twitch"
ATTR_DEFAULT_ENABLED = "default_enabled"
ATTR_FOLLOWING = "following"
ATTR_FOLLOWING_SINCE = "following_since"
ATTR_FOLLOWERS = "followers"
ATTR_GAME = "game"
ATTR_SUBSCRIBED = "subscribed"
ATTR_SUBSCRIBED_SINCE = "subscribed_since"
ATTR_SUBSCRIPTION_GIFTED = "subscription_is_gifted"
ATTR_TITLE = "title"
ATTR_VIEWS = "views"

CONF_CHANNELS = "channels"
DOMAIN = "twitch"
DEFAULT_NAME = "Twitch"
MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=30)


STATE_OFFLINE = "offline"
STATE_STREAMING = "streaming"

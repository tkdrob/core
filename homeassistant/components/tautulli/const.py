"""Constants for the Tautulli components."""
from datetime import timedelta

CONF_MONITORED_USERS = "monitored_users"

DATA_KEY_API = "api"
DATA_KEY_COORDINATOR = "coordinator"
DEFAULT_NAME = "Tautulli"
DEFAULT_PATH = ""
DEFAULT_PORT = "8181"
DEFAULT_SSL = False
DEFAULT_VERIFY_SSL = True
DOMAIN = "tautulli"

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=10)

SENSORS = {
    "LAN bandwidth",
    "Number of direct plays",
    "Number of direct streams",
    "Stream count",
    "Top Movie",
    "Top TV Show",
    "Top User",
    "Total bandwidth",
    "Transcode count",
    "WAN bandwidth",
}

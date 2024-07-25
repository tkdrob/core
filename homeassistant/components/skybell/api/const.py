"""Constants for the AIOSkybell."""

from enum import IntEnum, StrEnum
from logging import Logger, getLogger
from yarl import URL

from aiohttp.hdrs import ACCEPT, ACCEPT_ENCODING, CONNECTION, KEEP_ALIVE

CLOCK_LEEWAY = -20

JSON = "application/json"
LOGGER: Logger = getLogger(__package__)
BASE_URL = URL("https://api.skybell.network/api/v5/")


APP_VER = "1.222.2"
DEFAULT_HEADERS = {
    ACCEPT: f"{JSON}, text/plain, */*",
    ACCEPT_ENCODING: "gzip",
    CONNECTION: KEEP_ALIVE,
    "tz": "America/New_York",
    "x-skybell-lang": "en",
    "x-skybell-app": APP_VER,
}

REPO_URL = "https://github.com/tkdrob/aioskybell"


class HTTPMethod(StrEnum):
    """HTTPMethod Enum."""

    DELETE = "DELETE"
    GET = "GET"
    PATCH = "PATCH"
    POST = "POST"
    PUT = "PUT"


class ImageQuality(IntEnum):
    """Video recording quality enum."""

    low = 0
    medium = 1
    high = 2
    highest = 3


class LiveVolume(IntEnum):
    """Live speaker volume enum."""

    low = 0
    medium = 1
    high = 2


class Volume(IntEnum):
    """Speaker volume enum."""

    low = 0
    medium = 1
    high = 2
    off = -1


class EventType(StrEnum):
    """Event type enum."""

    BUTTON = "doorbell"
    DEMAND = "lstream"
    MOTION = "motion"
    NONE = ""
    RECORD = "record"
    SOUND = "sound"


class ToneType(StrEnum):
    """Tone type enum."""

    BUTTON = "button"
    MOTION = "motion"
    TEST = "test"

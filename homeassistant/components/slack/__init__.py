"""The slack integration."""
import logging

from aiohttp.client_exceptions import ClientError
from slack import WebClient
from slack.errors import SlackApiError
import voluptuous as vol

from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_PLATFORM, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import aiohttp_client, config_validation as cv, discovery
from homeassistant.helpers.typing import ConfigType

from .const import (
    ATTR_STATUS_EMOJI,
    ATTR_STATUS_EXPIRATION,
    ATTR_STATUS_TEXT,
    ATTR_URL,
    ATTR_USER_ID,
    DATA_CLIENT,
    DOMAIN,
    SERVICE_SET_STATUS,
)
from .coordinator import SlackDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.NOTIFY,
    Platform.NUMBER,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Slack component."""
    # Iterate all entries for notify to only get Slack
    if Platform.NOTIFY in config:
        for entry in config[Platform.NOTIFY]:
            if entry[CONF_PLATFORM] == DOMAIN:
                hass.async_create_task(
                    hass.config_entries.flow.async_init(
                        DOMAIN, context={"source": SOURCE_IMPORT}, data=entry
                    )
                )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Slack from a config entry."""
    session = aiohttp_client.async_get_clientsession(hass)
    slack = WebClient(token=entry.data[CONF_API_KEY], run_async=True, session=session)

    try:
        res = await slack.auth_test()
    except (SlackApiError, ClientError) as ex:
        if isinstance(ex, SlackApiError) and ex.response["error"] == "invalid_auth":
            _LOGGER.error("Invalid API key")
            return False
        raise ConfigEntryNotReady("Error while setting up integration") from ex
    data = {
        DATA_CLIENT: slack,
        ATTR_URL: res[ATTR_URL],
        ATTR_USER_ID: res[ATTR_USER_ID],
    }

    coordinator = SlackDataUpdateCoordinator(hass, slack, entry.data | data)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    hass.async_create_task(
        discovery.async_load_platform(
            hass,
            Platform.NOTIFY,
            DOMAIN,
            entry.data | data,
            hass.data[DOMAIN],
        )
    )

    await hass.config_entries.async_forward_entry_setups(
        entry, [platform for platform in PLATFORMS if platform != Platform.NOTIFY]
    )

    status_schema = cv.make_entity_service_schema(
        {
            vol.Optional(ATTR_STATUS_TEXT): cv.string,
            vol.Optional(ATTR_STATUS_EMOJI): cv.string,
            vol.Optional(ATTR_STATUS_EXPIRATION): cv.datetime,
        }
    )

    async def async_service_handler(service: ServiceCall) -> None:
        """Dispatch service calls to target entities."""
        params = dict(service.data)
        if _date := params.get(ATTR_STATUS_EXPIRATION):
            params[ATTR_STATUS_EXPIRATION] = int(_date.timestamp())

        if service.service == SERVICE_SET_STATUS:
            slack.users_profile_set(profile=params)

    hass.services.async_register(
        DOMAIN, SERVICE_SET_STATUS, async_service_handler, status_schema
    )

    return True

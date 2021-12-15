"""Support for Hangouts."""
import logging

from hangups.auth import GoogleAuthError
import voluptuous as vol

from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.helpers import dispatcher, intent

# We need an import from .config_flow, without it .config_flow is never loaded.
from .config_flow import HangoutsFlowHandler  # noqa: F401
from .const import (
    CONF_BOT,
    CONF_DEFAULT_CONVERSATIONS,
    CONF_ERROR_SUPPRESSED_CONVERSATIONS,
    CONF_INTENTS,
    CONF_REFRESH_TOKEN,
    DOMAIN,
    EVENT_HANGOUTS_CONNECTED,
    EVENT_HANGOUTS_CONVERSATIONS_CHANGED,
    EVENT_HANGOUTS_CONVERSATIONS_RESOLVED,
    MESSAGE_SCHEMA,
    SERVICE_RECONNECT,
    SERVICE_SEND_MESSAGE,
    SERVICE_UPDATE,
)
from .hangouts_bot import HangoutsBot
from .intents import HelpIntent

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config):
    """Set up a config entry."""
    try:
        bot = HangoutsBot(
            hass,
            config.data.get(CONF_REFRESH_TOKEN),
            hass.data[DOMAIN][CONF_INTENTS],
            hass.data[DOMAIN][CONF_DEFAULT_CONVERSATIONS],
            hass.data[DOMAIN][CONF_ERROR_SUPPRESSED_CONVERSATIONS],
        )
        hass.data[DOMAIN][CONF_BOT] = bot
    except GoogleAuthError as exception:
        _LOGGER.error("Hangouts failed to log in: %s", str(exception))
        return False

    dispatcher.async_dispatcher_connect(
        hass, EVENT_HANGOUTS_CONNECTED, bot.async_handle_update_users_and_conversations
    )

    dispatcher.async_dispatcher_connect(
        hass, EVENT_HANGOUTS_CONVERSATIONS_CHANGED, bot.async_resolve_conversations
    )

    dispatcher.async_dispatcher_connect(
        hass,
        EVENT_HANGOUTS_CONVERSATIONS_RESOLVED,
        bot.async_update_conversation_commands,
    )

    config.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, bot.async_handle_hass_stop)
    )

    await bot.async_connect()

    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_MESSAGE,
        bot.async_handle_send_message,
        schema=MESSAGE_SCHEMA,
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_UPDATE,
        bot.async_handle_update_users_and_conversations,
        schema=vol.Schema({}),
    )

    hass.services.async_register(
        DOMAIN, SERVICE_RECONNECT, bot.async_handle_reconnect, schema=vol.Schema({})
    )

    intent.async_register(hass, HelpIntent(hass))

    return True


async def async_unload_entry(hass, _):
    """Unload a config entry."""
    bot = hass.data[DOMAIN].pop(CONF_BOT)
    await bot.async_disconnect()
    return True

"""The Twitch integration."""
from __future__ import annotations

from aiohttp.client_exceptions import ClientConnectorError
from twitchio import Client, errors

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_TOKEN, EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import Event, HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.entity import DeviceInfo, Entity

from .const import ATTRIBUTION, CONF_CHANNELS, DEFAULT_NAME, DOMAIN

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Twitch from a config entry."""
    api = Client(entry.data[CONF_API_TOKEN])
    try:
        await api.validate()
    except (errors.HTTPException, ClientConnectorError) as ex:
        raise ConfigEntryNotReady(f"Failed connecting to twitch: {ex}") from ex
    except errors.AuthenticationError as ex:  # TODO
        raise ConfigEntryAuthFailed("Client ID or OAuth token is not valid") from ex
    if not entry.options:
        channel = (await api.search_channels(api.user_id))[0]
        users = [user.to_user.name.lower() for user in await channel.fetch_following()]
        users.append(api.nick)
        channel_data = {
            CONF_CHANNELS: {user: {"enabled": bool(user in api.nick)} for user in users}
        }
        hass.config_entries.async_update_entry(entry, options=channel_data)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = api
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    async def _async_on_hass_stop(event: Event) -> None:
        """HA is shutting down, close."""
        if hass.data[DOMAIN][entry.entry_id]:
            await hass.data[DOMAIN][entry.entry_id].close()

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _async_on_hass_stop)
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


class TwitchEntity(Entity):
    """Representation of a Twitch entity."""

    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        server_unique_id: str,
    ) -> None:
        """Initialize a Twitch entity."""
        # TODO maybe we can expose a url linking to the streamer's profile
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, server_unique_id)},
            manufacturer=DEFAULT_NAME,
            name=DEFAULT_NAME,
        )

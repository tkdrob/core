"""Support for the Twitch stream status."""
from __future__ import annotations

from re import sub

from aiohttp.client_exceptions import ClientConnectorError
from twitchio import ChannelInfo, Client, PartialUser, errors
import voluptuous as vol

import logging

from homeassistant.components.sensor import (
    DOMAIN as SENSOR_DOMAIN,
    PLATFORM_SCHEMA,
    SensorEntity,
)
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import CONF_CLIENT_ID, CONF_TOKEN
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import TwitchEntity
from .const import (
    ATTR_FOLLOWERS,
    ATTR_FOLLOWING,
    ATTR_FOLLOWING_SINCE,
    ATTR_GAME,
    ATTR_SUBSCRIBED,
    ATTR_SUBSCRIBED_SINCE,
    ATTR_SUBSCRIPTION_GIFTED,
    ATTR_TITLE,
    ATTR_VIEWS,
    CONF_CHANNELS,
    DOMAIN,
    STATE_OFFLINE,
    STATE_STREAMING,
)

# Deprecated in Home Assistant 2022.2
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_CLIENT_ID): cv.string,
        vol.Required(CONF_CHANNELS): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(CONF_TOKEN): cv.string,
    }
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Twitch sensor from yaml."""
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            SENSOR_DOMAIN, context={"source": SOURCE_IMPORT}, data=config
        )
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Twitch sensors."""
    api: Client = hass.data[DOMAIN][entry.entry_id]
    channels = [
        await api.fetch_channel(user)
        for user in entry.options[CONF_CHANNELS]
        if entry.options[CONF_CHANNELS][user]["enabled"]
    ]
    home_user = [channel.user for channel in channels if channel.user.id == api.user_id]
    async_add_entities(
        [TwitchSensor(x, api, home_user[0], entry.entry_id) for x in channels], True
    )


class TwitchSensor(TwitchEntity, SensorEntity):
    """Representation of an Twitch channel."""

    _attr_icon = "mdi:twitch"

    def __init__(
        self, channel: ChannelInfo, api: Client, home_user: PartialUser, entry_id: str
    ) -> None:
        """Initialize the sensor."""
        super().__init__(entry_id)
        self._api = api
        self._channel = channel
        self._home_user = home_user
        self._attr_name = channel.user.name.lower()
        self._attr_unique_id = f"{self.name}_{entry_id}"

    async def async_update(self) -> None:
        """Update sensor state."""
        attrs = {}
        try:
            if user := (await self._api.fetch_users(ids=[self._channel.user.id]))[0]:
                attrs[ATTR_VIEWS] = (user.view_count[0],)
                self._attr_entity_picture = user.profile_image
            if followers := await user.fetch_followers(full_body=True):
                attrs[ATTR_FOLLOWERS] = followers["total"]
            streams = await self._api.fetch_streams(user_ids=[self._channel.user.id])
            stream = streams[0] if streams else []
            self._attr_native_value = STATE_STREAMING if stream else STATE_OFFLINE
            if stream:
                attrs[ATTR_GAME] = stream.game_name
                attrs[ATTR_TITLE] = stream.title
                thumb = sub("{width}x{height}", "300x300", stream.thumbnail_url)
                self._attr_entity_picture = thumb
            if self._channel.user.id != self._api.user_id:
                attrs[ATTR_FOLLOWING] = False
                if follows := await self._home_user.fetch_follow(self._channel.user):
                    # TODO utc timezone disclose difference
                    attrs[ATTR_FOLLOWING] = True
                    attrs[ATTR_FOLLOWING_SINCE] = follows.followed_at
                    if subscription := await self._home_user.fetch_subscriptions(
                        userids=[self._channel.user.id]
                    ):
                        attrs[ATTR_SUBSCRIBED_SINCE] = subscription.created_at
                        attrs[ATTR_SUBSCRIPTION_GIFTED] = subscription.is_gift
                    attrs[ATTR_SUBSCRIBED] = subscription != []
        except (errors.HTTPException, ClientConnectorError):
            self._attr_available = False
            return
        except IndexError:
            pass
        self._attr_available = True
        self._attr_extra_state_attributes = attrs

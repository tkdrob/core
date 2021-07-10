"""Support for DLNA DMR (Device Media Renderer)."""
from __future__ import annotations

import asyncio
from datetime import timedelta
import functools
import logging

import aiohttp
from async_upnp_client import UpnpFactory
from async_upnp_client.aiohttp import AiohttpNotifyServer, AiohttpSessionRequester
from async_upnp_client.profiles.dlna import DeviceState, DmrDevice
import voluptuous as vol

from homeassistant.components.media_player import PLATFORM_SCHEMA, MediaPlayerEntity
from homeassistant.components.media_player.const import (
    SUPPORT_NEXT_TRACK,
    SUPPORT_PAUSE,
    SUPPORT_PLAY,
    SUPPORT_PLAY_MEDIA,
    SUPPORT_PREVIOUS_TRACK,
    SUPPORT_SEEK,
    SUPPORT_STOP,
    SUPPORT_VOLUME_MUTE,
    SUPPORT_VOLUME_SET,
)
from homeassistant.const import (
    CONF_NAME,
    CONF_URL,
    EVENT_HOMEASSISTANT_STOP,
    STATE_IDLE,
    STATE_OFF,
    STATE_ON,
    STATE_PAUSED,
    STATE_PLAYING,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.util import get_local_ip
import homeassistant.util.dt as dt_util

_LOGGER = logging.getLogger(__name__)

DLNA_DMR_DATA = "dlna_dmr"

DEFAULT_NAME = "DLNA Digital Media Renderer"
DEFAULT_LISTEN_PORT = 8301

CONF_LISTEN_IP = "listen_ip"
CONF_LISTEN_PORT = "listen_port"
CONF_CALLBACK_URL_OVERRIDE = "callback_url_override"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_URL): cv.string,
        vol.Optional(CONF_LISTEN_IP): cv.string,
        vol.Optional(CONF_LISTEN_PORT, default=DEFAULT_LISTEN_PORT): cv.port,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_CALLBACK_URL_OVERRIDE): cv.url,
    }
)


def catch_request_errors():
    """Catch asyncio.TimeoutError, aiohttp.ClientError errors."""

    def call_wrapper(func):
        """Call wrapper for decorator."""

        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            """Catch asyncio.TimeoutError, aiohttp.ClientError errors."""
            try:
                return await func(self, *args, **kwargs)
            except (asyncio.TimeoutError, aiohttp.ClientError):
                _LOGGER.error("Error during call %s", func.__name__)

        return wrapper

    return call_wrapper


async def async_start_event_handler(
    hass: HomeAssistant,
    server_host: str,
    server_port: int,
    requester,
    callback_url_override: str | None = None,
):
    """Register notify view."""
    hass_data = hass.data[DLNA_DMR_DATA]
    if "event_handler" in hass_data:
        return hass_data["event_handler"]

    # start event handler
    server = AiohttpNotifyServer(
        requester,
        listen_port=server_port,
        listen_host=server_host,
        callback_url=callback_url_override,
    )
    await server.start_server()
    _LOGGER.info("UPNP/DLNA event handler listening, url: %s", server.callback_url)
    hass_data["notify_server"] = server
    hass_data["event_handler"] = server.event_handler

    # register for graceful shutdown
    async def async_stop_server(event):
        """Stop server."""
        _LOGGER.debug("Stopping UPNP/DLNA event handler")
        await server.stop_server()

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, async_stop_server)

    return hass_data["event_handler"]


async def async_setup_platform(
    hass: HomeAssistant, config, async_add_entities, discovery_info=None
):
    """Set up DLNA DMR platform."""
    if config.get(CONF_URL) is not None:
        url = config[CONF_URL]
        name = config.get(CONF_NAME)
    elif discovery_info is not None:
        url = discovery_info["ssdp_description"]
        name = discovery_info.get("name")

    if DLNA_DMR_DATA not in hass.data:
        hass.data[DLNA_DMR_DATA] = {}

    if "lock" not in hass.data[DLNA_DMR_DATA]:
        hass.data[DLNA_DMR_DATA]["lock"] = asyncio.Lock()

    # build upnp/aiohttp requester
    session = async_get_clientsession(hass)
    requester = AiohttpSessionRequester(session, True)

    # ensure event handler has been started
    async with hass.data[DLNA_DMR_DATA]["lock"]:
        server_host = config.get(CONF_LISTEN_IP)
        if server_host is None:
            server_host = get_local_ip()
        server_port = config.get(CONF_LISTEN_PORT, DEFAULT_LISTEN_PORT)
        callback_url_override = config.get(CONF_CALLBACK_URL_OVERRIDE)
        event_handler = await async_start_event_handler(
            hass, server_host, server_port, requester, callback_url_override
        )

    # create upnp device
    factory = UpnpFactory(requester, non_strict=True)
    try:
        upnp_device = await factory.async_create_device(url)
    except (asyncio.TimeoutError, aiohttp.ClientError) as err:
        raise PlatformNotReady() from err

    # wrap with DmrDevice
    dlna_device = DmrDevice(upnp_device, event_handler)

    # create our own device
    device = DlnaDmrDevice(dlna_device, name)
    _LOGGER.debug("Adding device: %s", device)
    async_add_entities([device], True)


class DlnaDmrDevice(MediaPlayerEntity):
    """Representation of a DLNA DMR device."""

    def __init__(self, dmr_device, name=None):
        """Initialize DLNA DMR device."""
        self._device = self._attr_name = dmr_device
        self._attr_unique_id = dmr_device.udn

        self._subscription_renew_time = None
        self._attr_supported_features = 0
        if dmr_device.has_volume_level:
            self._attr_supported_features |= SUPPORT_VOLUME_SET
        if dmr_device.has_volume_mute:
            self._attr_supported_features |= SUPPORT_VOLUME_MUTE
        if dmr_device.has_play:
            self._attr_supported_features |= SUPPORT_PLAY
        if dmr_device.has_pause:
            self._attr_supported_features |= SUPPORT_PAUSE
        if dmr_device.has_stop:
            self._attr_supported_features |= SUPPORT_STOP
        if dmr_device.has_previous:
            self._attr_supported_features |= SUPPORT_PREVIOUS_TRACK
        if dmr_device.has_next:
            self._attr_supported_features |= SUPPORT_NEXT_TRACK
        if dmr_device.has_play_media:
            self._attr_supported_features |= SUPPORT_PLAY_MEDIA
        if dmr_device.has_seek_rel_time:
            self._attr_supported_features |= SUPPORT_SEEK

    async def async_added_to_hass(self):
        """Handle addition."""
        self._device.on_event = self._on_event

        # Register unsubscribe on stop
        bus = self.hass.bus
        bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, self._async_on_hass_stop)

    async def _async_on_hass_stop(self, event):
        """Event handler on Home Assistant stop."""
        async with self.hass.data[DLNA_DMR_DATA]["lock"]:
            await self._device.async_unsubscribe_services()

    async def async_update(self):
        """Retrieve the latest data."""
        was_available = self.available

        try:
            await self._device.async_update()
            self._attr_available = True
        except (asyncio.TimeoutError, aiohttp.ClientError):
            self._attr_available = False
            _LOGGER.debug("Device unavailable")
            return

        # do we need to (re-)subscribe?
        now = dt_util.utcnow()
        should_renew = (
            self._subscription_renew_time and now >= self._subscription_renew_time
        )
        if should_renew or not was_available and self.available:
            try:
                timeout = await self._device.async_subscribe_services()
                self._subscription_renew_time = dt_util.utcnow() + timeout / 2
            except (asyncio.TimeoutError, aiohttp.ClientError):
                self._attr_available = False
                _LOGGER.debug("Could not (re)subscribe")
        if not self.available:
            self._attr_state = STATE_OFF
        elif self._device.state is None:
            self._attr_state = STATE_ON
        elif self._device.state == DeviceState.PLAYING:
            self._attr_state = STATE_PLAYING
        elif self._device.state == DeviceState.PAUSED:
            self._attr_state = STATE_PAUSED
        else:
            self._attr_state = STATE_IDLE

        if self._device.has_volume_level:
            self._attr_volume_level = self._device.volume_level
        else:
            self._attr_volume_level = 0
        self._attr_is_volume_muted = self._device.is_volume_muted

        self._attr_media_title = self._device.media_title
        self._attr_media_image_url = self._device.media_image_url
        self._attr_media_duration = self._device.media_duration
        self._attr_media_position = self._device.media_position
        self._attr_media_position_updated_at = self._device.media_position_updated_at

    def _on_event(self, service, state_variables):
        """State variable(s) changed, let home-assistant know."""
        self.schedule_update_ha_state()

    @catch_request_errors()
    async def async_set_volume_level(self, volume):
        """Set volume level, range 0..1."""
        await self._device.async_set_volume_level(volume)

    @catch_request_errors()
    async def async_mute_volume(self, mute):
        """Mute the volume."""
        desired_mute = bool(mute)
        await self._device.async_mute_volume(desired_mute)

    @catch_request_errors()
    async def async_media_pause(self):
        """Send pause command."""
        if not self._device.can_pause:
            _LOGGER.debug("Cannot do Pause")
            return

        await self._device.async_pause()

    @catch_request_errors()
    async def async_media_play(self):
        """Send play command."""
        if not self._device.can_play:
            _LOGGER.debug("Cannot do Play")
            return

        await self._device.async_play()

    @catch_request_errors()
    async def async_media_stop(self):
        """Send stop command."""
        if not self._device.can_stop:
            _LOGGER.debug("Cannot do Stop")
            return

        await self._device.async_stop()

    @catch_request_errors()
    async def async_media_seek(self, position):
        """Send seek command."""
        if not self._device.can_seek_rel_time:
            _LOGGER.debug("Cannot do Seek/rel_time")
            return

        time = timedelta(seconds=position)
        await self._device.async_seek_rel_time(time)

    @catch_request_errors()
    async def async_play_media(self, media_type, media_id, **kwargs):
        """Play a piece of media."""
        _LOGGER.debug("Playing media: %s, %s, %s", media_type, media_id, kwargs)
        title = "Home Assistant"

        # Stop current playing media
        if self._device.can_stop:
            await self.async_media_stop()

        # Queue media
        await self._device.async_set_transport_uri(media_id, title)
        await self._device.async_wait_for_can_play()

        # If already playing, no need to call Play
        if self._device.state == DeviceState.PLAYING:
            return

        # Play it
        await self.async_media_play()

    @catch_request_errors()
    async def async_media_previous_track(self):
        """Send previous track command."""
        if not self._device.can_previous:
            _LOGGER.debug("Cannot do Previous")
            return

        await self._device.async_previous()

    @catch_request_errors()
    async def async_media_next_track(self):
        """Send next track command."""
        if not self._device.can_next:
            _LOGGER.debug("Cannot do Next")
            return

        await self._device.async_next()

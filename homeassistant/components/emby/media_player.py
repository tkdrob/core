"""Support to interface with the Emby API."""
import logging

from pyemby import EmbyServer
import voluptuous as vol

from homeassistant.components.media_player import PLATFORM_SCHEMA, MediaPlayerEntity
from homeassistant.components.media_player.const import (
    MEDIA_TYPE_CHANNEL,
    MEDIA_TYPE_MOVIE,
    MEDIA_TYPE_MUSIC,
    MEDIA_TYPE_TVSHOW,
    SUPPORT_NEXT_TRACK,
    SUPPORT_PAUSE,
    SUPPORT_PLAY,
    SUPPORT_PREVIOUS_TRACK,
    SUPPORT_SEEK,
    SUPPORT_STOP,
)
from homeassistant.const import (
    CONF_API_KEY,
    CONF_HOST,
    CONF_PORT,
    CONF_SSL,
    DEVICE_DEFAULT_NAME,
    EVENT_HOMEASSISTANT_START,
    EVENT_HOMEASSISTANT_STOP,
    STATE_IDLE,
    STATE_OFF,
    STATE_PAUSED,
    STATE_PLAYING,
)
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt_util

_LOGGER = logging.getLogger(__name__)

MEDIA_TYPE_TRAILER = "trailer"
MEDIA_TYPE_GENERIC_VIDEO = "video"

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 8096
DEFAULT_SSL_PORT = 8920
DEFAULT_SSL = False

SUPPORT_EMBY = (
    SUPPORT_PAUSE
    | SUPPORT_PREVIOUS_TRACK
    | SUPPORT_NEXT_TRACK
    | SUPPORT_STOP
    | SUPPORT_SEEK
    | SUPPORT_PLAY
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_API_KEY): cv.string,
        vol.Optional(CONF_HOST, default=DEFAULT_HOST): cv.string,
        vol.Optional(CONF_PORT): cv.port,
        vol.Optional(CONF_SSL, default=DEFAULT_SSL): cv.boolean,
    }
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Emby platform."""

    host = config.get(CONF_HOST)
    key = config.get(CONF_API_KEY)
    port = config.get(CONF_PORT)
    ssl = config[CONF_SSL]

    if port is None:
        port = DEFAULT_SSL_PORT if ssl else DEFAULT_PORT

    _LOGGER.debug("Setting up Emby server at: %s:%s", host, port)

    emby = EmbyServer(host, key, port, ssl, hass.loop)

    active_emby_devices = {}
    inactive_emby_devices = {}

    @callback
    def device_update_callback(data):
        """Handle devices which are added to Emby."""
        new_devices = []
        active_devices = []
        for dev_id in emby.devices:
            active_devices.append(dev_id)
            if (
                dev_id not in active_emby_devices
                and dev_id not in inactive_emby_devices
            ):
                new = EmbyDevice(emby, dev_id)
                active_emby_devices[dev_id] = new
                new_devices.append(new)

            elif (
                dev_id in inactive_emby_devices and emby.devices[dev_id].state != "Off"
            ):
                add = inactive_emby_devices.pop(dev_id)
                active_emby_devices[dev_id] = add
                _LOGGER.debug("Showing %s, item: %s", dev_id, add)
                add.set_available(True)

        if new_devices:
            _LOGGER.debug("Adding new devices: %s", new_devices)
            async_add_entities(new_devices, True)

    @callback
    def device_removal_callback(data):
        """Handle the removal of devices from Emby."""
        if data in active_emby_devices:
            rem = active_emby_devices.pop(data)
            inactive_emby_devices[data] = rem
            _LOGGER.debug("Inactive %s, item: %s", data, rem)
            rem.set_available(False)

    @callback
    def start_emby(event):
        """Start Emby connection."""
        emby.start()

    async def stop_emby(event):
        """Stop Emby connection."""
        await emby.stop()

    emby.add_new_devices_callback(device_update_callback)
    emby.add_stale_devices_callback(device_removal_callback)

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, start_emby)
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, stop_emby)


class EmbyDevice(MediaPlayerEntity):
    """Representation of an Emby device."""

    _attr_should_poll = False

    def __init__(self, emby, device_id):
        """Initialize the Emby device."""
        _LOGGER.debug("New Emby Device initialized with ID: %s", device_id)
        self.emby = emby
        self.device_id = self._attr_unique_id = device_id
        self.device = self.emby.devices[self.device_id]
        self._attr_name = f"Emby {self.device.name}" or DEVICE_DEFAULT_NAME
        if self.device.supports_remote_control:
            self._attr_supported_features = SUPPORT_EMBY

    async def async_added_to_hass(self):
        """Register callback."""
        self.emby.add_update_callback(self.async_update_callback, self.device_id)

    @callback
    def async_update_callback(self, msg):
        """Handle device updates."""
        state = self.device.state
        if state == "Paused":
            self._attr_state = STATE_PAUSED
        elif state == "Playing":
            self._attr_state = STATE_PLAYING
        elif state == "Idle":
            self._attr_state = STATE_IDLE
        elif state == "Off":
            self._attr_state = STATE_OFF
        # Check if we should update progress
        if self.device.media_position:
            if self.device.media_position != self.media_position:
                self._attr_media_position = self.device.media_position
                media_status_received = dt_util.utcnow()
        elif not self.device.is_nowplaying:
            # No position, but we have an old value and are still playing
            self._attr_media_position = None
            media_status_received = None
        self._attr_app_name = self.device.username
        media_type = self.device.media_type
        self._attr_media_content_type = None
        if media_type == "Episode":
            self._attr_media_content_type = MEDIA_TYPE_TVSHOW
        elif media_type == "Movie":
            self._attr_media_content_type = MEDIA_TYPE_MOVIE
        elif media_type == "Trailer":
            self._attr_media_content_type = MEDIA_TYPE_TRAILER
        elif media_type == "Music":
            self._attr_media_content_type = MEDIA_TYPE_MUSIC
        elif media_type == "Video":
            self._attr_media_content_type = MEDIA_TYPE_GENERIC_VIDEO
        elif media_type == "Audio":
            self._attr_media_content_type = MEDIA_TYPE_MUSIC
        elif media_type == "TvChannel":
            self._attr_media_content_type = MEDIA_TYPE_CHANNEL
        self._attr_media_content_id = self.device.media_id
        self._attr_media_duration = self.device.media_runtime
        self._attr_media_position_updated_at = media_status_received
        self._attr_media_image_url = self.device.media_image_url
        self._attr_media_title = self.device.media_title
        self._attr_media_season = self.device.media_season
        self._attr_media_series_title = self.device.media_series_title
        self._attr_media_episode = self.device.media_episode
        self._attr_media_album_name = self.device.media_album_name
        self._attr_media_artist = self.device.media_artist
        self._attr_media_album_artist = self.device.media_album_artist
        self.async_write_ha_state()

    def set_available(self, value):
        """Set available property."""
        self._attr_available = value

    async def async_media_play(self):
        """Play media."""
        await self.device.media_play()

    async def async_media_pause(self):
        """Pause the media player."""
        await self.device.media_pause()

    async def async_media_stop(self):
        """Stop the media player."""
        await self.device.media_stop()

    async def async_media_next_track(self):
        """Send next track command."""
        await self.device.media_next()

    async def async_media_previous_track(self):
        """Send next track command."""
        await self.device.media_previous()

    async def async_media_seek(self, position):
        """Send seek command."""
        await self.device.media_seek(position)

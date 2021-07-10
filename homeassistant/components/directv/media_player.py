"""Support for the DirecTV receivers."""
from __future__ import annotations

import logging

from directv import DIRECTV

from homeassistant.components.media_player import (
    DEVICE_CLASS_RECEIVER,
    MediaPlayerEntity,
)
from homeassistant.components.media_player.const import (
    MEDIA_TYPE_CHANNEL,
    MEDIA_TYPE_MOVIE,
    MEDIA_TYPE_MUSIC,
    MEDIA_TYPE_TVSHOW,
    SUPPORT_NEXT_TRACK,
    SUPPORT_PAUSE,
    SUPPORT_PLAY,
    SUPPORT_PLAY_MEDIA,
    SUPPORT_PREVIOUS_TRACK,
    SUPPORT_STOP,
    SUPPORT_TURN_OFF,
    SUPPORT_TURN_ON,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_OFF, STATE_PAUSED, STATE_PLAYING
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_MEDIA_CURRENTLY_RECORDING,
    ATTR_MEDIA_RATING,
    ATTR_MEDIA_RECORDED,
    ATTR_MEDIA_START_TIME,
    DOMAIN,
)
from .entity import DIRECTVEntity

_LOGGER = logging.getLogger(__name__)

KNOWN_MEDIA_TYPES = [MEDIA_TYPE_MOVIE, MEDIA_TYPE_MUSIC, MEDIA_TYPE_TVSHOW]

SUPPORT_DTV = (
    SUPPORT_PAUSE
    | SUPPORT_TURN_ON
    | SUPPORT_TURN_OFF
    | SUPPORT_PLAY_MEDIA
    | SUPPORT_STOP
    | SUPPORT_NEXT_TRACK
    | SUPPORT_PREVIOUS_TRACK
    | SUPPORT_PLAY
)

SUPPORT_DTV_CLIENT = (
    SUPPORT_PAUSE
    | SUPPORT_PLAY_MEDIA
    | SUPPORT_STOP
    | SUPPORT_NEXT_TRACK
    | SUPPORT_PREVIOUS_TRACK
    | SUPPORT_PLAY
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> bool:
    """Set up the DirecTV config entry."""
    dtv = hass.data[DOMAIN][entry.entry_id]
    entities = []

    for location in dtv.device.locations:
        entities.append(
            DIRECTVMediaPlayer(
                dtv=dtv,
                name=str.title(location.name),
                address=location.address,
            )
        )

    async_add_entities(entities, True)


class DIRECTVMediaPlayer(DIRECTVEntity, MediaPlayerEntity):
    """Representation of a DirecTV receiver on the network."""

    def __init__(self, *, dtv: DIRECTV, name: str, address: str = "0") -> None:
        """Initialize DirecTV media player."""
        super().__init__(
            dtv=dtv,
            address=address,
        )

        self._attr_unique_id = self._device_id
        self._attr_name = name
        self._attr_device_class = DEVICE_CLASS_RECEIVER
        self._attr_available = False
        self._attr_assumed_state = None

        self._is_recorded = None
        self._is_standby = True
        self._last_position = None
        self._last_update = None
        self._program = None
        self._attr_supported_features = (
            SUPPORT_DTV_CLIENT if self._is_client else SUPPORT_DTV
        )

    async def async_update(self):
        """Retrieve latest state."""
        state = await self.dtv.state(self._address)
        self._attr_available = state.available
        self._is_standby = state.standby
        self._program = state.program

        if self._is_standby:
            self._attr_assumed_state = False
            self._is_recorded = None
            self._last_position = None
            self._last_update = None
            paused = None
        elif self._program is not None:
            paused = self._last_position == self._program.position
            self._is_recorded = self._program.recorded
            self._last_position = self._program.position
            self._last_update = state.at
            self._attr_assumed_state = self._is_recorded

        if self._is_standby:
            self._attr_state = STATE_OFF
            self._attr_extra_state_attributes = {}
        else:
            # For recorded media we can determine if it is paused or not.
            # For live media we're unable to determine and will always return
            # playing instead.
            if paused:
                self._attr_state = STATE_PAUSED
            else:
                self._attr_state = STATE_PLAYING
            self._attr_extra_state_attributes = {
                ATTR_MEDIA_CURRENTLY_RECORDING: self.media_currently_recording,
                ATTR_MEDIA_RATING: self.media_rating,
                ATTR_MEDIA_RECORDED: self.media_recorded,
                ATTR_MEDIA_START_TIME: self.media_start_time,
            }
        self.update_media()

    def update_media(self):
        """Update media attributes."""
        if self._is_standby or self._program is None:
            self._attr_media_content_id = None
            self._attr_media_content_type = None
            self._attr_media_duration = None
            self._attr_media_artist = None
            self._attr_media_album_name = None
            self._attr_media_series_title = None
            self._attr_media_channel = None
            self._attr_source = None
        else:
            if self._program.program_type in KNOWN_MEDIA_TYPES:
                self._attr_media_content_type = self._program.program_type
            else:
                self._attr_media_content_type = MEDIA_TYPE_MOVIE
            self._attr_media_content_id = self._program.program_id
            self._attr_media_duration = self._program.duration
            self._attr_media_artist = self._program.music_artist
            self._attr_media_album_name = self._program.music_album
            self._attr_media_series_title = self._program.episode_title
            self._attr_media_channel = (
                f"{self._program.channel_name} ({self._program.channel})"
            )
            self._attr_source = self._program.channel
        if self._is_standby:
            self._attr_media_position = None
            self._attr_media_position_updated_at = None
        else:
            self._attr_media_position = self._last_position
            self._attr_media_position_updated_at = self._last_update

    @property
    def media_title(self):
        """Return the title of current playing media."""
        if self._is_standby or self._program is None:
            return None

        if self.media_content_type == MEDIA_TYPE_MUSIC:
            return self._program.music_title

        return self._program.title

    @property
    def media_currently_recording(self):
        """If the media is currently being recorded or not."""
        if self._is_standby or self._program is None:
            return None

        return self._program.recording

    @property
    def media_rating(self):
        """TV Rating of the current playing media."""
        if self._is_standby or self._program is None:
            return None

        return self._program.rating

    @property
    def media_recorded(self):
        """If the media was recorded or live."""
        if self._is_standby:
            return None

        return self._is_recorded

    @property
    def media_start_time(self):
        """Start time the program aired."""
        if self._is_standby or self._program is None:
            return None

        return dt_util.as_local(self._program.start_time)

    async def async_turn_on(self):
        """Turn on the receiver."""
        if self._is_client:
            raise NotImplementedError()

        _LOGGER.debug("Turn on %s", self.name)
        await self.dtv.remote("poweron", self._address)

    async def async_turn_off(self):
        """Turn off the receiver."""
        if self._is_client:
            raise NotImplementedError()

        _LOGGER.debug("Turn off %s", self.name)
        await self.dtv.remote("poweroff", self._address)

    async def async_media_play(self):
        """Send play command."""
        _LOGGER.debug("Play on %s", self.name)
        await self.dtv.remote("play", self._address)

    async def async_media_pause(self):
        """Send pause command."""
        _LOGGER.debug("Pause on %s", self.name)
        await self.dtv.remote("pause", self._address)

    async def async_media_stop(self):
        """Send stop command."""
        _LOGGER.debug("Stop on %s", self.name)
        await self.dtv.remote("stop", self._address)

    async def async_media_previous_track(self):
        """Send rewind command."""
        _LOGGER.debug("Rewind on %s", self.name)
        await self.dtv.remote("rew", self._address)

    async def async_media_next_track(self):
        """Send fast forward command."""
        _LOGGER.debug("Fast forward on %s", self.name)
        await self.dtv.remote("ffwd", self._address)

    async def async_play_media(self, media_type, media_id, **kwargs):
        """Select input source."""
        if media_type != MEDIA_TYPE_CHANNEL:
            _LOGGER.error(
                "Invalid media type %s. Only %s is supported",
                media_type,
                MEDIA_TYPE_CHANNEL,
            )
            return

        _LOGGER.debug("Changing channel on %s to %s", self.name, media_id)
        await self.dtv.tune(media_id, self._address)

"""Dune HD implementation of the media player."""
from __future__ import annotations

from typing import Any, Final

from pdunehd import DuneHDPlayer
import voluptuous as vol

from homeassistant.components.media_player import (
    PLATFORM_SCHEMA as PARENT_PLATFORM_SCHEMA,
    MediaPlayerEntity,
)
from homeassistant.components.media_player.const import (
    SUPPORT_NEXT_TRACK,
    SUPPORT_PAUSE,
    SUPPORT_PLAY,
    SUPPORT_PREVIOUS_TRACK,
    SUPPORT_TURN_OFF,
    SUPPORT_TURN_ON,
)
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    STATE_OFF,
    STATE_ON,
    STATE_PAUSED,
    STATE_PLAYING,
)
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import ATTR_MANUFACTURER, DEFAULT_NAME, DOMAIN

CONF_SOURCES: Final = "sources"

PLATFORM_SCHEMA: Final = PARENT_PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_SOURCES): vol.Schema({cv.string: cv.string}),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)

DUNEHD_PLAYER_SUPPORT: Final[int] = (
    SUPPORT_PAUSE
    | SUPPORT_TURN_ON
    | SUPPORT_TURN_OFF
    | SUPPORT_PREVIOUS_TRACK
    | SUPPORT_NEXT_TRACK
    | SUPPORT_PLAY
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Dune HD media player platform."""
    host: str = config[CONF_HOST]

    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_IMPORT}, data={CONF_HOST: host}
        )
    )


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Add Dune HD entities from a config_entry."""
    unique_id = entry.entry_id

    player: str = hass.data[DOMAIN][entry.entry_id]

    async_add_entities([DuneHDPlayerEntity(player, DEFAULT_NAME, unique_id)], True)


class DuneHDPlayerEntity(MediaPlayerEntity):
    """Implementation of the Dune HD player."""

    _attr_supported_features = DUNEHD_PLAYER_SUPPORT

    def __init__(self, player: DuneHDPlayer, name: str, unique_id: str) -> None:
        """Initialize entity to control Dune HD."""
        self._player = player
        self._attr_name = name
        self._state: dict[str, Any] = {}
        self._attr_unique_id = unique_id
        self._attr_device_info = {
            "identifiers": {(DOMAIN, unique_id)},
            "name": DEFAULT_NAME,
            "manufacturer": ATTR_MANUFACTURER,
        }

    def update(self) -> bool:
        """Update internal status of the entity."""
        self._state = self._player.update_state()
        self.__update_title()
        self._attr_available = len(self._state) > 0
        if "playback_position" in self._state:
            self._attr_state = STATE_PLAYING
        elif self._state.get("player_state") in (
            "playing",
            "buffering",
            "photo_viewer",
        ):
            self._attr_state = STATE_PLAYING
        elif int(self._state.get("playback_speed", 1234)) == 0:
            self._attr_state = STATE_PAUSED
        elif self._state.get("player_state") == "navigator":
            self._attr_state = STATE_ON
        else:
            self._attr_state = STATE_OFF
        self.__update_title()
        self._attr_volume_level = int(self._state.get("playback_volume", 0)) / 100
        self._attr_is_volume_muted = int(self._state.get("playback_mute", 0)) == 1
        return True

    def volume_up(self) -> None:
        """Volume up media player."""
        self._state = self._player.volume_up()

    def volume_down(self) -> None:
        """Volume down media player."""
        self._state = self._player.volume_down()

    def mute_volume(self, mute: bool) -> None:
        """Mute/unmute player volume."""
        self._state = self._player.mute(mute)

    def turn_off(self) -> None:
        """Turn off media player."""
        self._attr_media_title = None
        self._state = self._player.turn_off()

    def turn_on(self) -> None:
        """Turn off media player."""
        self._state = self._player.turn_on()

    def media_play(self) -> None:
        """Play media player."""
        self._state = self._player.play()

    def media_pause(self) -> None:
        """Pause media player."""
        self._state = self._player.pause()

    def __update_title(self) -> None:
        if self._state.get("player_state") == "bluray_playback":
            self._attr_media_title = "Blu-Ray"
        elif self._state.get("player_state") == "photo_viewer":
            self._attr_media_title = "Photo Viewer"
        elif self._state.get("playback_url"):
            self._attr_media_title = self._state["playback_url"].split("/")[-1]
        else:
            self._attr_media_title = None

    def media_previous_track(self) -> None:
        """Send previous track command."""
        self._state = self._player.previous_track()

    def media_next_track(self) -> None:
        """Send next track command."""
        self._state = self._player.next_track()

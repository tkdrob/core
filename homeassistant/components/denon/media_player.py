"""Support for Denon Network Receivers."""
import logging
import telnetlib

import voluptuous as vol

from homeassistant.components.media_player import PLATFORM_SCHEMA, MediaPlayerEntity
from homeassistant.components.media_player.const import (
    SUPPORT_NEXT_TRACK,
    SUPPORT_PAUSE,
    SUPPORT_PLAY,
    SUPPORT_PREVIOUS_TRACK,
    SUPPORT_SELECT_SOURCE,
    SUPPORT_STOP,
    SUPPORT_TURN_OFF,
    SUPPORT_TURN_ON,
    SUPPORT_VOLUME_MUTE,
    SUPPORT_VOLUME_SET,
)
from homeassistant.const import CONF_HOST, CONF_NAME, STATE_OFF, STATE_ON
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Music station"

SUPPORT_DENON = (
    SUPPORT_VOLUME_SET
    | SUPPORT_VOLUME_MUTE
    | SUPPORT_TURN_ON
    | SUPPORT_TURN_OFF
    | SUPPORT_SELECT_SOURCE
)
SUPPORT_MEDIA_MODES = (
    SUPPORT_PAUSE
    | SUPPORT_STOP
    | SUPPORT_PREVIOUS_TRACK
    | SUPPORT_NEXT_TRACK
    | SUPPORT_PLAY
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)

NORMAL_INPUTS = {
    "Cd": "CD",
    "Dvd": "DVD",
    "Blue ray": "BD",
    "TV": "TV",
    "Satellite / Cable": "SAT/CBL",
    "Game": "GAME",
    "Game2": "GAME2",
    "Video Aux": "V.AUX",
    "Dock": "DOCK",
}

MEDIA_MODES = {
    "Tuner": "TUNER",
    "Media server": "SERVER",
    "Ipod dock": "IPOD",
    "Net/USB": "NET/USB",
    "Rapsody": "RHAPSODY",
    "Napster": "NAPSTER",
    "Pandora": "PANDORA",
    "LastFM": "LASTFM",
    "Flickr": "FLICKR",
    "Favorites": "FAVORITES",
    "Internet Radio": "IRADIO",
    "USB/IPOD": "USB/IPOD",
}

# Sub-modes of 'NET/USB'
# {'USB': 'USB', 'iPod Direct': 'IPD', 'Internet Radio': 'IRP',
#  'Favorites': 'FVP'}


def setup_platform(
    hass, config, add_entities: AddEntitiesCallback, discovery_info=None
):
    """Set up the Denon platform."""
    denon = DenonDevice(config[CONF_NAME], config[CONF_HOST])

    if denon.update():
        add_entities([denon], True)


class DenonDevice(MediaPlayerEntity):
    """Representation of a Denon device."""

    def __init__(self, name, host):
        """Initialize the Denon device."""
        self._attr_name = name
        self._host = host
        self._volume = 0
        # Initial value 60dB, changed if we get a MVMAX
        self._volume_max = 60
        source_list = NORMAL_INPUTS.copy()
        source_list.update(MEDIA_MODES)
        self._attr_source_list = sorted(source_list)

        self._should_setup_sources = True

    def _setup_sources(self, telnet):
        # NSFRN - Network name
        nsfrn = self.telnet_request(telnet, "NSFRN ?")[len("NSFRN ") :]
        if nsfrn:
            self._attr_name = nsfrn

        # SSFUN - Configured sources with (optional) names
        self._attr_source_list = {}
        for line in self.telnet_request(telnet, "SSFUN ?", all_lines=True):
            ssfun = line[len("SSFUN") :].split(" ", 1)

            source = ssfun[0]
            if len(ssfun) == 2 and ssfun[1]:
                configured_name = ssfun[1]
            else:
                # No name configured, reusing the source name
                configured_name = source

            self._attr_source_list[configured_name] = source

        # SSSOD - Deleted sources
        for line in self.telnet_request(telnet, "SSSOD ?", all_lines=True):
            source, status = line[len("SSSOD") :].split(" ", 1)
            if status == "DEL":
                for pretty_name, name in self.source_list.items():
                    if source == name:
                        del self._attr_source_list[pretty_name]
                        break

    @classmethod
    def telnet_request(cls, telnet, command, all_lines=False):
        """Execute `command` and return the response."""
        _LOGGER.debug("Sending: %s", command)
        telnet.write(command.encode("ASCII") + b"\r")
        lines = []
        while True:
            line = telnet.read_until(b"\r", timeout=0.2)
            if not line:
                break
            lines.append(line.decode("ASCII").strip())
            _LOGGER.debug("Received: %s", line)

        if all_lines:
            return lines
        return lines[0] if lines else ""

    def telnet_command(self, command):
        """Establish a telnet connection and sends `command`."""
        telnet = telnetlib.Telnet(self._host)
        _LOGGER.debug("Sending: %s", command)
        telnet.write(command.encode("ASCII") + b"\r")
        telnet.read_very_eager()  # skip response
        telnet.close()

    def update(self):
        """Get the latest details from the device."""
        try:
            telnet = telnetlib.Telnet(self._host)
        except OSError:
            return False

        if self._should_setup_sources:
            self._setup_sources(telnet)
            self._should_setup_sources = False

        pwstate = self.telnet_request(telnet, "PW?")
        if pwstate == "PWSTANDBY":
            self._attr_state = STATE_OFF
        else:
            self._attr_state = STATE_ON if pwstate == "PWON" else None

        for line in self.telnet_request(telnet, "MV?", all_lines=True):
            if line.startswith("MVMAX "):
                # only grab two digit max, don't care about any half digit
                self._volume_max = int(line[len("MVMAX ") : len("MVMAX XX")])
                continue
            if line.startswith("MV"):
                self._volume = int(line[len("MV") :])
                self._attr_volume_level = self._volume / self._volume_max
        self._attr_is_volume_muted = self.telnet_request(telnet, "MU?") == "MUON"
        mediasource = self.telnet_request(telnet, "SI?")[len("SI") :]
        for pretty_name, name in self.source_list.items():
            if mediasource == name:
                self._attr_source = pretty_name
        if mediasource in MEDIA_MODES.values():
            self._attr_supported_features = SUPPORT_DENON | SUPPORT_MEDIA_MODES
            self._attr_media_title = ""
            answer_codes = [
                "NSE0",
                "NSE1X",
                "NSE2X",
                "NSE3X",
                "NSE4",
                "NSE5",
                "NSE6",
                "NSE7",
                "NSE8",
            ]
            for line in self.telnet_request(telnet, "NSE", all_lines=True):
                self._attr_media_title += f"{line[len(answer_codes.pop(0)) :]}\n"
        else:
            self._attr_media_title = self.source
            self._attr_supported_features = SUPPORT_DENON

        telnet.close()
        return True

    def turn_off(self):
        """Turn off media player."""
        self.telnet_command("PWSTANDBY")

    def volume_up(self):
        """Volume up media player."""
        self.telnet_command("MVUP")

    def volume_down(self):
        """Volume down media player."""
        self.telnet_command("MVDOWN")

    def set_volume_level(self, volume):
        """Set volume level, range 0..1."""
        self.telnet_command(f"MV{round(volume * self._volume_max):02}")

    def mute_volume(self, mute):
        """Mute (true) or unmute (false) media player."""
        mute_status = "ON" if mute else "OFF"
        self.telnet_command(f"MU{mute_status})")

    def media_play(self):
        """Play media player."""
        self.telnet_command("NS9A")

    def media_pause(self):
        """Pause media player."""
        self.telnet_command("NS9B")

    def media_stop(self):
        """Pause media player."""
        self.telnet_command("NS9C")

    def media_next_track(self):
        """Send the next track command."""
        self.telnet_command("NS9D")

    def media_previous_track(self):
        """Send the previous track command."""
        self.telnet_command("NS9E")

    def turn_on(self):
        """Turn the media player on."""
        self.telnet_command("PWON")

    def select_source(self, source):
        """Select input source."""
        self.telnet_command(f"SI{self.source_list.get(source)}")

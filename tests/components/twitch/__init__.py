"""Tests for the Twitch component."""
from unittest.mock import AsyncMock, patch
from homeassistant.components.twitch.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_API_TOKEN
from tests.common import MockConfigEntry

CONF_DATA = {CONF_API_TOKEN: "abc123"}


def create_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Create Twitch entry in Home Assistant."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="123456",
        data=CONF_DATA,
    )
    entry.add_to_hass(hass)
    return entry


def patch_twitch():
    """Patch twitch."""
    mocked_twitch = AsyncMock()
    mocked_twitch.id = "123456"
    return patch(
        "homeassistant.components.twitch.config_flow.Client",
        return_value=mocked_twitch,
    )


def patch_twitch_users():
    "Patch twitch users."
    return patch("homeassistant.components.twitch.config_flow.Client.fetch_users")

"""Support for the Skybell HD Doorbell."""

from __future__ import annotations

import asyncio
from dataclasses import fields
import os
from typing import cast
from zoneinfo import ZoneInfo

from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.util.dt as dt_util

from .api import Client
from .api.exceptions import SkybellAuthenticationException, SkybellException
from .coordinator import (
    SkybellConfigEntry,
    SkybellData,
    SkybellDataUpdateCoordinator,
    SkybellEventsUpdateCoordinator,
)

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.CAMERA,
    Platform.LIGHT,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: SkybellConfigEntry) -> bool:
    """Set up Skybell from a config entry."""

    def remove_pickle() -> None:
        """Remove old pickle file."""
        _file = hass.config.path(f"./skybell_{entry.unique_id}.pickle")
        if os.path.exists(_file):
            os.remove(_file)

    tz = cast(ZoneInfo, dt_util.get_default_time_zone())
    if entry.data.get("AccessToken"):  # Remove after 6 releases
        api = Client(auth=entry.data, session=async_get_clientsession(hass), tzinfo=tz)
    else:
        api = Client(
            username=entry.data[CONF_EMAIL],
            password=entry.data[CONF_PASSWORD],
            session=async_get_clientsession(hass),
            tzinfo=tz,
        )
        await hass.async_add_executor_job(remove_pickle)
    try:
        devices = await api.initialize()
    except SkybellAuthenticationException as ex:
        raise ConfigEntryAuthFailed from ex
    except (TimeoutError, SkybellException) as ex:
        raise ConfigEntryNotReady(ex) from ex

    if not entry.data.get("AccessToken"):  # Remove after 6 releases
        hass.config_entries.async_update_entry(
            entry, data=entry.data | api.auth.dict(), unique_id=api.user.account_id
        )
    data = SkybellData(
        devices=tuple(SkybellDataUpdateCoordinator(hass, device) for device in devices),
        events=tuple(
            SkybellEventsUpdateCoordinator(hass, device) for device in devices
        ),
    )
    await asyncio.gather(
        *(
            coordinator.async_config_entry_first_refresh()
            for field in fields(data)
            for coordinator in getattr(data, field.name)
        )
    )
    entry.runtime_data = data
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: SkybellConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

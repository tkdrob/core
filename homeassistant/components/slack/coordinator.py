"""Data update coordinator for the Slack integration."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

from slack import WebClient
from slack.errors import SlackApiError

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import homeassistant.util.dt as dt_util

from .const import (
    ATTR_SNOOZE,
    ATTR_STATUS_EXPIRATION,
    ATTR_URL,
    ATTR_USER_ID,
    DOMAIN,
    LOGGER,
)


class SlackDataUpdateCoordinator(DataUpdateCoordinator):
    """Data update coordinator for the Slack integration."""

    config_entry: ConfigEntry

    def __init__(
        self, hass: HomeAssistant, client: WebClient, data: dict[str, str | WebClient]
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
        )
        self.client = client
        self._data = data
        self.dnd_end: datetime | None = None
        self.profile: dict[str, str] = {}
        self.presence = False

    async def _async_update_data(self) -> None:
        """Fetch data from API endpoint."""
        try:
            _time, _profile, presence = await asyncio.gather(
                *[
                    self.client.dnd_info(),
                    self.client.users_profile_get(),
                    self.client.users_getPresence(user=self.user_id),
                ]
            )
        except SlackApiError as ex:
            raise UpdateFailed from ex
        _profile = _profile["profile"]
        self.dnd_end = (
            dt_util.utc_from_timestamp(_time[ATTR_SNOOZE])
            if _time.get(ATTR_SNOOZE)
            else None
        )
        self.presence = presence["presence"] == "active"
        if (expire := _profile[ATTR_STATUS_EXPIRATION]) and expire > 0:
            _profile[ATTR_STATUS_EXPIRATION] = dt_util.utc_from_timestamp(expire)
        else:
            _profile[ATTR_STATUS_EXPIRATION] = None
        self.profile = _profile

    @property
    def url(self) -> str:
        """Return team url."""
        return self._data[ATTR_URL]

    @property
    def user_id(self) -> str:
        """Return user id."""
        return self._data[ATTR_USER_ID]

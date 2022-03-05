"""Data update coordinator for the Twitch integration."""
from __future__ import annotations

from datetime import timedelta
import functools as ft

from twitchAPI.twitch import Twitch, TwitchAuthorizationException

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, LOGGER


class TwitchDataUpdateCoordinator(DataUpdateCoordinator):
    """Data update coordinator for the Twitch integration."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: Twitch,
        user,
        channels: list,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
        )
        self.client = client
        self.users: dict[str, dict[str, str]] = {}
        self.user = user
        self.channels = [channel["id"] for channel in channels]
        self.streams: dict[str, dict[str, str]] = {}
        self.follows: dict[str, dict[str, str]] = {}
        self.followers: dict[str, int] = {}
        self.subs: dict[str, dict[str, list[dict[str, str | bool]]]] = {}

    async def _async_update_data(self) -> None:
        """Get the latest data from Twitch."""
        try:
            data = await self.hass.async_add_executor_job(
                ft.partial(self.client.get_users, user_ids=self.channels)
            )
            self.users = {channel["id"]: channel for channel in data["data"]}
            self.streams = {
                stream["user_id"]: stream
                for stream in (
                    await self.hass.async_add_executor_job(
                        ft.partial(self.client.get_streams, user_id=self.channels)
                    )
                )["data"]
            }
            data = [
                (
                    await self.hass.async_add_executor_job(
                        ft.partial(
                            self.client.get_users_follows,
                            from_id=self.user,
                            to_id=channel,
                        )
                    )
                )["data"]
                for channel in self.channels
                if channel != self.user
            ]
            self.follows = {
                channel[0]["to_id"]: channel[0] for channel in data if len(channel)
            }
            self.followers = {
                channel: (
                    await self.hass.async_add_executor_job(
                        ft.partial(self.client.get_users_follows, to_id=channel)
                    )
                )["total"]
                for channel in self.channels
            }
            if self.user:
                self.subs = {
                    channel: (
                        await self.hass.async_add_executor_job(
                            ft.partial(
                                self.client.check_user_subscription,
                                user_id=self.user,
                                broadcaster_id=channel,
                            )
                        )
                    )
                    for channel in self.channels
                    if channel != self.user
                }

        except TwitchAuthorizationException:
            LOGGER.error("Invalid client ID or client secret")

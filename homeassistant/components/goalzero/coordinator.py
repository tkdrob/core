"""Data update coordinator for the Goal Zero integration."""

from datetime import timedelta

from goalzero import Yeti, exceptions

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import LOGGER


class GoalZeroDataUpdateCoordinator(DataUpdateCoordinator):
    """Data update coordinator for the Goal Zero integration."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, api: Yeti, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=entry.title,
            update_interval=timedelta(seconds=30),
        )
        self.api = api
        self.config_entry = entry

    async def _async_update_data(self) -> None:
        """Fetch data from API endpoint."""
        try:
            await self.api.get_state()
        except exceptions.ConnectError as err:
            raise UpdateFailed("Failed to communicate with device") from err

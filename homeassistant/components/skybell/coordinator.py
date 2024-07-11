"""Data update coordinator for the Skybell integration."""

from dataclasses import dataclass
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import Client
from .api.device import SkybellDevice
from .api.exceptions import SkybellAuthenticationException, SkybellException
from .const import LOGGER

type SkybellConfigEntry = ConfigEntry[SkybellData]


class SkybellDataUpdateCoordinator(DataUpdateCoordinator[None]):
    """Data update coordinator for the Skybell integration."""

    config_entry: SkybellConfigEntry
    _update_interval = timedelta(minutes=15)

    def __init__(self, hass: HomeAssistant, device: SkybellDevice) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=device.info.name,
            update_interval=self._update_interval,
        )
        self.device = device

    async def _async_update_data(self) -> None:
        """Fetch data from API endpoint."""
        try:
            await self._fetch_data()
        except SkybellAuthenticationException as ex:
            raise ConfigEntryAuthFailed from ex
        except (TimeoutError, SkybellException) as ex:
            raise UpdateFailed(ex) from ex

    async def _fetch_data(self) -> None:
        """Fetch the actual data."""
        await self.device.async_update()


class SkybellEventsUpdateCoordinator(SkybellDataUpdateCoordinator):
    """Data update coordinator for the Skybell integration."""

    _update_interval = timedelta(seconds=30)

    async def _fetch_data(self) -> None:
        """Fetch the actual data."""
        await self.device.async_get_events()


@dataclass(kw_only=True, slots=True)
class SkybellData:
    """Skybell data type."""

    devices: tuple[SkybellDataUpdateCoordinator, ...]
    events: tuple[SkybellEventsUpdateCoordinator, ...]

    @property
    def client(self) -> Client:
        """Return the client object."""
        return self.devices[0].device.client

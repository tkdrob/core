"""Data update coordinator for the Dremel 3D Printer integration."""

from datetime import timedelta
from typing import Any

from dremel3dpy import Dremel3DPrinter

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
import homeassistant.util.dt as dt_util

from .const import DOMAIN, LOGGER


class Dremel3DPrinterDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Dremel 3D Printer data."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, api: Dremel3DPrinter) -> None:
        """Initialize Dremel 3D Printer data update coordinator."""
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=10),
        )
        self.printer_offline = False
        self.api = api

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via APIs."""
        try:
            await self.hass.async_add_executor_job(self.api.refresh)
        except RuntimeError:
            if not self.printer_offline:
                LOGGER.debug("Unable to refresh printer information: Printer offline")
                self.printer_offline = True
        else:
            self.printer_offline = False

        return {
            "last_read_time": dt_util.utcnow(),
        }

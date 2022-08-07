"""Support for Dremel 3D Printer buttons."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import Dremel3DPrinterEntity

BUTTON_TYPES: tuple[ButtonEntityDescription, ...] = (
    ButtonEntityDescription(
        key="pause_job",
        name="Pause job",
    ),
    ButtonEntityDescription(
        key="resume_job",
        name="Resume job",
    ),
    ButtonEntityDescription(
        key="stop_job",
        name="Stop job",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Dremel 3D Printer control buttons."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    # async_add_entities(Dremel3DPrinterButton(coordinator, description) for description in BUTTON_TYPES) TODO

    async_add_entities(
        [
            Dremel3DPrinterPauseJobButton(coordinator, BUTTON_TYPES[0]),
            Dremel3DPrinterResumeJobButton(coordinator, BUTTON_TYPES[1]),
            Dremel3DPrinterStopJobButton(coordinator, BUTTON_TYPES[2]),
        ]
    )


class Dremel3DPrinterPauseJobButton(Dremel3DPrinterEntity, ButtonEntity):
    """Represent a Dremel 3D Printer base button."""

    async def async_press(self) -> None:
        """Handle the pause button press."""
        if self._api.is_running():
            self.hass.async_add_executor_job(self._api.pause_print)
        else:
            raise InvalidPrinterState("Printer is not printing")


class Dremel3DPrinterResumeJobButton(Dremel3DPrinterEntity, ButtonEntity):
    """Resume the active job."""

    async def async_press(self) -> None:
        """Handle the resume button press."""
        if self._api.is_paused():
            self.hass.async_add_executor_job(self._api.resume_print)
        else:
            raise InvalidPrinterState("Printer is not currently paused")


class Dremel3DPrinterStopJobButton(Dremel3DPrinterEntity, ButtonEntity):
    """Stop the active job."""

    async def async_press(self) -> None:
        """Handle the button press."""
        if self._api.is_printing():
            self.hass.async_add_executor_job(self._api.stop_print)
        else:
            raise InvalidPrinterState("Printer is not currently printing")


class InvalidPrinterState(HomeAssistantError):
    """Service attempted in invalid state."""

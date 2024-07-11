"""Button entity support for the Skybell HD Doorbell."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api.device import SkybellDevice
from .coordinator import SkybellConfigEntry
from .entity import SkybellEntity


@dataclass(frozen=True, kw_only=True)
class SkybellButtonEntityDescription(ButtonEntityDescription):
    """Describes a Skybell button entity."""

    entity_category = EntityCategory.CONFIG
    entity_registry_enabled_default = False
    press_fn: Callable[[SkybellDevice], Awaitable]


BUTTON_TYPES: tuple[SkybellButtonEntityDescription, ...] = (
    SkybellButtonEntityDescription(
        key="play_tone",
        translation_key="play_tone",
        device_class=ButtonDeviceClass.IDENTIFY,
        press_fn=lambda d: d.play_tone(),
    ),
    SkybellButtonEntityDescription(
        key="reboot",
        translation_key="reboot",
        device_class=ButtonDeviceClass.RESTART,
        press_fn=lambda d: d.reboot(),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SkybellConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Skybell button."""
    async_add_entities(
        SkybellButton(coordinator, description)
        for description in BUTTON_TYPES
        for coordinator in entry.runtime_data.devices
        if not coordinator.device.info.shared_read_only
    )


class SkybellButton(SkybellEntity, ButtonEntity):
    """A button implementation for Skybell devices."""

    entity_description: SkybellButtonEntityDescription

    async def async_press(self) -> None:
        """Press the button."""
        await self.entity_description.press_fn(self._device)

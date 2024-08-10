"""Select entity support for the Skybell HD Doorbell."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import IntEnum
from typing import Any, cast

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .api import Client
from .api.const import ImageQuality, LiveVolume, Volume
from .api.device import SkybellDevice
from .coordinator import SkybellConfigEntry
from .entity import SkybellEntity


@dataclass(frozen=True, kw_only=True)
class SkybellSelectEntityDescription(SelectEntityDescription):
    """Describes a Skybell select entity."""

    available_fn: Callable[[SkybellDevice], bool] = lambda _: True
    current_option_fn: Callable[[SkybellDevice], str] | None = None
    entity_registry_enabled_default = False
    options_fn: Callable[[Client], list[str]]
    select_fn: Callable[[SkybellDevice, str], Awaitable]


SELECT_TYPES: tuple[SkybellSelectEntityDescription, ...] = (
    SkybellSelectEntityDescription(
        key="button_tone",
        translation_key="button_tone",
        current_option_fn=lambda d: d.client.tone_file_dict[d.info.tones.button.file],
        entity_category=EntityCategory.CONFIG,
        options_fn=lambda c: list(c.all_tones),
        select_fn=lambda d, o: d.set_tone(o, "button"),
    ),
    SkybellSelectEntityDescription(
        key="image_quality",
        translation_key="image_quality",
        available_fn=lambda d: d.info.settings.image_quality is not None,
        current_option_fn=lambda d: cast(IntEnum, d.info.settings.image_quality).name,
        entity_category=EntityCategory.CONFIG,
        options_fn=lambda _: [i.name for i in ImageQuality],
        select_fn=lambda d, o: d.set_settings(image_quality=ImageQuality[o]),
    ),
    SkybellSelectEntityDescription(
        key="live_volume",
        translation_key="live_volume",
        available_fn=lambda d: d.info.settings.speaker_volume is not None,
        current_option_fn=lambda d: cast(IntEnum, d.info.settings.speaker_volume).name,
        entity_category=EntityCategory.CONFIG,
        options_fn=lambda _: [i.name for i in LiveVolume],
        select_fn=lambda d, o: d.set_settings(speaker_volume=Volume[o]),
    ),
    SkybellSelectEntityDescription(
        key="motion_chime_volume",
        translation_key="motion_chime_volume",
        current_option_fn=lambda d: d.info.settings.motion_chime_volume.name,
        entity_category=EntityCategory.CONFIG,
        options_fn=lambda _: [i.name for i in Volume],
        select_fn=lambda d, o: d.set_settings(motion_chime_volume=Volume[o]),
    ),
    SkybellSelectEntityDescription(
        key="motion_tone",
        translation_key="motion_tone",
        current_option_fn=lambda d: d.client.tone_file_dict[d.info.tones.motion.file],
        entity_category=EntityCategory.CONFIG,
        options_fn=lambda c: list(c.all_tones),
        select_fn=lambda d, o: d.set_tone(o, "motion"),
    ),
    SkybellSelectEntityDescription(
        key="outdoor_chime_volume",
        translation_key="outdoor_chime_volume",
        current_option_fn=lambda d: d.info.settings.outdoor_chime_volume.name,
        entity_category=EntityCategory.CONFIG,
        options_fn=lambda _: [i.name for i in Volume],
        select_fn=lambda d, o: d.set_settings(outdoor_chime_volume=Volume[o]),
    ),
    SkybellSelectEntityDescription(
        key="test_tone",
        translation_key="test_tone",
        entity_category=EntityCategory.CONFIG,
        options_fn=lambda c: list(c.tones),
        select_fn=lambda d, o: d.set_tone(o, "test"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SkybellConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Skybell select."""
    async_add_entities(
        SkybellSelect(coordinator, description)
        for description in SELECT_TYPES
        for coordinator in entry.runtime_data.devices
        if not coordinator.device.info.shared_read_only
    )


class SkybellSelect(SkybellEntity, SelectEntity, RestoreEntity):
    """A select implementation for Skybell devices."""

    entity_description: SkybellSelectEntityDescription

    def __init__(self, *args: Any) -> None:
        """Initialize."""
        super().__init__(*args)
        self._attr_assumed_state = not self.entity_description.current_option_fn
        self._attr_options = self.entity_description.options_fn(self._device.client)

    async def async_added_to_hass(self) -> None:
        """Call when the select is added to hass."""
        if self.assumed_state:
            if state := await self.async_get_last_state():
                self._attr_current_option = state.state
            else:
                self._attr_current_option = None
        await super().async_added_to_hass()

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return super().available and self.entity_description.available_fn(self._device)

    @property
    def current_option(self) -> str | None:
        """Return the selected entity option to represent the entity state."""
        if self.entity_description.current_option_fn:
            return self.entity_description.current_option_fn(self._device)
        return super().current_option

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self.entity_description.select_fn(self._device, option)
        self._attr_current_option = option
        self.coordinator.async_set_updated_data(None)

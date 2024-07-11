"""Switch support for the Skybell HD Doorbell."""

from __future__ import annotations

from collections.abc import Callable
import dataclasses
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api.device import SkybellDevice
from .api.models import BasicMotion, ChangeableMotionSettings, ChangeableSettings
from .coordinator import SkybellConfigEntry
from .entity import SkybellEntity


@dataclasses.dataclass(frozen=True, kw_only=True)
class SkybellSwitchEntityDescription(SwitchEntityDescription):
    """Class to describe a Skybell switch."""

    available_fn: Callable[[SkybellDevice], bool] = (
        lambda d: not d.info.shared_read_only
    )
    turn_on_fn: ChangeableSettings | ChangeableMotionSettings
    turn_off_fn: ChangeableSettings | ChangeableMotionSettings
    is_on_fn: Callable[[SkybellDevice], bool]


SWITCH_TYPES: tuple[SkybellSwitchEntityDescription, ...] = (
    SkybellSwitchEntityDescription(
        key="do_not_disturb",
        translation_key="do_not_disturb",
        turn_on_fn=ChangeableSettings(indoor_chime=False),
        turn_off_fn=ChangeableSettings(indoor_chime=True),
        is_on_fn=lambda d: not d.info.settings.indoor_chime,
    ),
    SkybellSwitchEntityDescription(
        key="do_not_ring",
        translation_key="do_not_ring",
        turn_on_fn=ChangeableSettings(outdoor_chime=False),
        turn_off_fn=ChangeableSettings(outdoor_chime=True),
        is_on_fn=lambda d: not d.info.settings.outdoor_chime,
    ),
    SkybellSwitchEntityDescription(
        key="motion_sensor",
        translation_key="motion_sensor",
        turn_on_fn=ChangeableMotionSettings(
            basic_motion=BasicMotion(motion_record=True)
        ),
        turn_off_fn=ChangeableMotionSettings(
            basic_motion=BasicMotion(motion_record=False)
        ),
        is_on_fn=lambda d: d.info.settings.basic_motion.motion_record,
        entity_registry_enabled_default=False,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SkybellConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the SkyBell switch."""
    async_add_entities(
        SkybellSwitch(coordinator, description)
        for coordinator in entry.runtime_data.devices
        for description in SWITCH_TYPES
    )


class SkybellSwitch(SkybellEntity, SwitchEntity):
    """A switch implementation for Skybell devices."""

    entity_description: SkybellSwitchEntityDescription

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the switch."""
        option = self.entity_description.turn_on_fn
        await self._device.set_settings(option)
        self.coordinator.async_set_updated_data(None)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the switch."""
        option = self.entity_description.turn_off_fn
        await self._device.set_settings(option)
        self.coordinator.async_set_updated_data(None)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return super().available and self.entity_description.available_fn(self._device)

    @property
    def is_on(self) -> bool:
        """Return true if entity is on."""
        return self.entity_description.is_on_fn(self._device)

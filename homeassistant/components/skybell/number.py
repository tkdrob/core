"""Number entity support for the Skybell HD Doorbell."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.const import PERCENTAGE, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api.device import ChangeableSettings
from .api.models import Settings
from .coordinator import SkybellConfigEntry
from .entity import SkybellEntity


@dataclass(frozen=True, kw_only=True)
class SkybellNumberEntityDescription(NumberEntityDescription):
    """Describes a Skybell number entity."""

    entity_category = EntityCategory.CONFIG
    entity_registry_enabled_default = False
    native_max_value = 100
    native_min_value = 0
    native_unit_of_measurement = PERCENTAGE
    mode = NumberMode.SLIDER
    value_fn: Callable[[Settings], float]
    set_value_fn: Callable[[int], ChangeableSettings]


NUMBER_TYPES: tuple[SkybellNumberEntityDescription, ...] = (
    SkybellNumberEntityDescription(
        key="motion_sensitivity",
        translation_key="motion_sensitivity",
        value_fn=lambda s: s.motion_sensitivity / 10,
        set_value_fn=lambda i: ChangeableSettings(motion_sensitivity=i * 10),
    ),
    SkybellNumberEntityDescription(
        key="pir_sensitivity",
        translation_key="pir_sensitivity",
        value_fn=lambda s: s.pir_sensitivity / 10,
        set_value_fn=lambda i: ChangeableSettings(pir_sensitivity=i * 10),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SkybellConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Skybell number."""
    async_add_entities(
        SkybellNumber(coordinator, description)
        for description in NUMBER_TYPES
        for coordinator in entry.runtime_data.devices
        if not coordinator.device.info.shared_read_only
    )


class SkybellNumber(SkybellEntity, NumberEntity):
    """A number implementation for Skybell devices."""

    entity_description: SkybellNumberEntityDescription

    @property
    def native_value(self) -> float | None:
        """Return the state of the entity."""
        return self.entity_description.value_fn(self._device.info.settings)

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        await self._device.set_settings(
            self.entity_description.set_value_fn(int(value))
        )
        self.coordinator.async_set_updated_data(None)

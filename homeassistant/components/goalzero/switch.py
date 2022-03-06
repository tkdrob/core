"""Support for Goal Zero Yeti Switches."""
from __future__ import annotations

from typing import Any, cast

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import YetiEntity
from .const import DOMAIN
from .coordinator import GoalZeroDataUpdateCoordinator

SWITCH_TYPES: tuple[SwitchEntityDescription, ...] = (
    SwitchEntityDescription(
        key="v12PortStatus",
        name="12V Port Status",
    ),
    SwitchEntityDescription(
        key="usbPortStatus",
        name="USB Port Status",
    ),
    SwitchEntityDescription(
        key="acPortStatus",
        name="AC Port Status",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Goal Zero Yeti switch."""
    async_add_entities(
        YetiSwitch(hass.data[DOMAIN][entry.entry_id], description)
        for description in SWITCH_TYPES
    )


class YetiSwitch(YetiEntity, SwitchEntity):
    """Representation of a Goal Zero Yeti switch."""

    coordinator: GoalZeroDataUpdateCoordinator

    def __init__(
        self,
        coordinator: GoalZeroDataUpdateCoordinator,
        description: SwitchEntityDescription,
    ) -> None:
        """Initialize a Goal Zero Yeti switch."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_name = f"{coordinator.config_entry.title} {description.name}"
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}/{description.key}"

    @property
    def is_on(self) -> bool:
        """Return state of the switch."""
        return cast(bool, self.coordinator.api.data[self.entity_description.key] == 1)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the switch."""
        payload = {self.entity_description.key: 0}
        await self.coordinator.api.post_state(payload=payload)
        self.coordinator.async_set_updated_data(data=payload)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the switch."""
        payload = {self.entity_description.key: 1}
        await self.coordinator.api.post_state(payload=payload)
        self.coordinator.async_set_updated_data(data=payload)

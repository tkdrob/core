"""Slack platform for select component."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import SlackEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Slack select."""
    async_add_entities([SlackNumberEntity(hass.data[DOMAIN][entry.entry_id], None)])


class SlackNumberEntity(SlackEntity, NumberEntity):
    """Representation of a Slack select."""

    _attr_native_value = 60
    _attr_native_min_value = 0
    _attr_native_step = 1
    _attr_name = "Do not disturb"
    _attr_icon = "mdi:clock"

    async def async_set_native_value(self, value: float) -> None:
        """Set native value."""
        await self._client.dnd_setSnooze(num_minutes=value)

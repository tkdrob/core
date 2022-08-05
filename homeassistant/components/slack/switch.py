"""Slack platform for switch component."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import SlackEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Slack switch."""
    async_add_entities(
        [
            SlackSwitchEntity(
                hass.data[DOMAIN][entry.entry_id],
                SwitchEntityDescription(
                    key="active",
                    name="Active",
                ),
            )
        ]
    )


class SlackSwitchEntity(SlackEntity, SwitchEntity):
    """Representation of a Slack switch."""

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the switch."""
        await self._client.users_setPresence(presence="away")

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the switch."""
        await self._client.users_setPresence(presence="auto")

    @property
    def is_on(self) -> bool:
        """Return true if user is active."""
        return self.coordinator.presence

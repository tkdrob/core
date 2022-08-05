"""Slack platform for sensor component."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Union, cast

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import ATTR_STATUS_EXPIRATION, ATTR_STATUS_TEXT, DOMAIN
from .coordinator import SlackDataUpdateCoordinator
from .entity import SlackEntity


@dataclass
class SlackSensorEntityDescription(SensorEntityDescription):
    """Class to describe a Slack sensor."""

    value_fn: Callable[
        [SlackDataUpdateCoordinator], StateType | datetime
    ] = lambda val: cast(Union[StateType, datetime], val)
    entity_picture_fn: Callable[[dict[str, str]], str | None] = lambda val: val.get("")


SENSOR_TYPES: tuple[SlackSensorEntityDescription, ...] = (
    SlackSensorEntityDescription(
        key="do_not_disturb_until",
        name="Do not disturb until",
        icon="mdi:clock",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda coordinator: coordinator.dnd_end,
        entity_picture_fn=lambda _: None,
    ),
    SlackSensorEntityDescription(
        key="status",
        name="Status",
        value_fn=lambda coordinator: coordinator.profile.get(ATTR_STATUS_TEXT, ""),
        entity_picture_fn=lambda profile: profile.get("image_72"),
    ),
    SlackSensorEntityDescription(
        key="status_expiration",
        name="Status expiration",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda coordinator: coordinator.profile[ATTR_STATUS_EXPIRATION],
        entity_picture_fn=lambda _: None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Slack sensor."""
    async_add_entities(
        SlackSensorEntity(hass.data[DOMAIN][entry.entry_id], description)
        for description in SENSOR_TYPES
    )


class SlackSensorEntity(SlackEntity, SensorEntity):
    """Representation of a Slack sensor."""

    entity_description: SlackSensorEntityDescription

    @property
    def native_value(self) -> StateType | datetime:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.coordinator)

    @property
    def entity_picture(self) -> str | None:
        """Return the entity picture to use in the frontend, if any."""
        return self.entity_description.entity_picture_fn(self.coordinator.profile)

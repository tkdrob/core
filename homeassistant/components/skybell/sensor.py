"""Sensor support for Skybell Doorbells."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import cast

from homeassistant.components.automation import automations_with_entity
from homeassistant.components.script import scripts_with_entity
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    EntityCategory,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.issue_registry import IssueSeverity, async_create_issue
from homeassistant.helpers.typing import StateType

from .api.const import EventType
from .api.device import SkybellDevice
from .api.models import DeviceTelemetry
from .const import DOMAIN
from .coordinator import SkybellConfigEntry
from .entity import SkybellEntity


@dataclass(frozen=True, kw_only=True)
class SkybellSensorEntityDescription(SensorEntityDescription):
    """Class to describe a Skybell sensor."""

    entity_registry_enabled_default = False
    value_fn: Callable[[SkybellDevice], StateType | datetime]


SENSOR_TYPES: tuple[SkybellSensorEntityDescription, ...] = (
    SkybellSensorEntityDescription(
        key="last_button_event",
        translation_key="last_button_event",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda d: d.latest_activity_datetime(EventType.BUTTON),
    ),
    SkybellSensorEntityDescription(
        key="last_motion_event",
        translation_key="last_motion_event",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda d: d.latest_activity_datetime(EventType.MOTION),
    ),
    SkybellSensorEntityDescription(
        key="last_check_in",
        translation_key="last_check_in",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.info.updated_at,
    ),
    SkybellSensorEntityDescription(
        key="wifi_ssid",
        translation_key="wifi_ssid",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.info.device_settings.ESSID,
    ),
    SkybellSensorEntityDescription(
        key="wifi_status",
        translation_key="wifi_status",
        entity_category=EntityCategory.DIAGNOSTIC,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        value_fn=lambda d: cast(DeviceTelemetry, d.info.telemetry).signal_level,
    ),
)

DEPRECATED_SENSORS: tuple[SkybellSensorEntityDescription, ...] = (
    SkybellSensorEntityDescription(
        key="chime_level",
        translation_key="chime_level",
        value_fn=lambda d: d.info.settings.outdoor_chime_volume,
    ),
    SkybellSensorEntityDescription(
        key="motion_threshold",
        translation_key="motion_threshold",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.info.settings.motion_sensitivity,
    ),
    SkybellSensorEntityDescription(
        key="video_profile",
        translation_key="video_profile",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.info.settings.image_quality,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SkybellConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Skybell sensor."""
    ent_reg = er.async_get(hass)
    devices = [c.device for c in entry.runtime_data.devices]
    coordinators = entry.runtime_data.devices
    entities = [
        SkybellSensor(coordinator, description)
        for coordinator in coordinators
        for description in SENSOR_TYPES
    ]

    for device_id in (d.info.device_id for d in devices):
        for description in DEPRECATED_SENSORS:
            # Check to see if this entity already exists.
            # If not, do not create a new one.
            entity_id = ent_reg.async_get_entity_id(
                Platform.SENSOR,
                DOMAIN,
                f"{device_id}_{description.key}",
            )
            if entity_id and (entity_entry := ent_reg.async_get(entity_id)):
                if entity_entry.disabled:
                    # If the entity exists and is disabled then we want to remove
                    # the entity so that the user is using the new number entity instead.
                    ent_reg.async_remove(entity_id)
                else:
                    entities.extend(
                        SkybellSensor(coordinator, description)
                        for coordinator in coordinators
                    )
                    async_create_issue(
                        hass,
                        DOMAIN,
                        f"deprecated_sensor_{entity_id}",
                        breaks_in_ha_version="2025.2.0",
                        is_fixable=True,
                        severity=IssueSeverity.WARNING,
                        translation_key="deprecated_skybell_sensor",
                        translation_placeholders={"entity": entity_id},
                    )
                    entity_automations = automations_with_entity(hass, entity_id)
                    entity_scripts = scripts_with_entity(hass, entity_id)
                    for item in entity_automations + entity_scripts:
                        async_create_issue(
                            hass,
                            DOMAIN,
                            f"deprecated_sensor_{entity_id}_{item}",
                            breaks_in_ha_version="2025.2.0",
                            is_fixable=True,
                            is_persistent=True,
                            severity=IssueSeverity.WARNING,
                            translation_key="deprecated_sensor_automation",
                            translation_placeholders={
                                "entity": entity_id,
                                "info": item,
                            },
                        )

    async_add_entities(entities)


class SkybellSensor(SkybellEntity, SensorEntity):
    """A sensor implementation for Skybell devices."""

    entity_description: SkybellSensorEntityDescription

    @property
    def native_value(self) -> StateType | datetime:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self._device)

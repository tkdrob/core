"""Platform for Garmin Connect integration."""
from __future__ import annotations

import logging

from garminconnect_ha import (
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ATTRIBUTION, CONF_ID
from homeassistant.core import HomeAssistant

from .alarm_util import calculate_next_active_alarms
from .const import ATTRIBUTION, DOMAIN, GARMIN_ENTITY_LIST

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up Garmin Connect sensor based on a config entry."""
    garmin_data = hass.data[DOMAIN][entry.entry_id]
    unique_id = entry.data[CONF_ID]

    try:
        await garmin_data.async_update()
    except (
        GarminConnectConnectionError,
        GarminConnectAuthenticationError,
        GarminConnectTooManyRequestsError,
    ) as err:
        _LOGGER.error("Error occurred during Garmin Connect Client update: %s", err)
    except Exception:  # pylint: disable=broad-except
        _LOGGER.exception("Unknown error occurred during Garmin Connect Client update")

    entities = []
    for (
        sensor_type,
        (name, unit, icon, device_class, enabled_by_default),
    ) in GARMIN_ENTITY_LIST.items():

        _LOGGER.debug(
            "Registering entity: %s, %s, %s, %s, %s, %s",
            sensor_type,
            name,
            unit,
            icon,
            device_class,
            enabled_by_default,
        )
        entities.append(
            GarminConnectSensor(
                garmin_data,
                unique_id,
                sensor_type,
                name,
                unit,
                icon,
                device_class,
                enabled_by_default,
            )
        )

    async_add_entities(entities, True)


class GarminConnectSensor(SensorEntity):
    """Representation of a Garmin Connect Sensor."""

    def __init__(
        self,
        data,
        unique_id,
        sensor_type,
        name,
        unit,
        icon,
        device_class,
        enabled_default: bool = True,
    ):
        """Initialize."""
        self._data = data
        self._attr_unique_id = f"{unique_id}_{sensor_type}"
        self._type = sensor_type
        self._attr_name = name
        self._attr_unit_of_measurement = unit
        self._attr_icon = icon
        self._attr_device_class = device_class
        self._attr_entity_registry_enabled_default = enabled_default
        self._attr_available = True
        self._attr_device_info = {
            "identifiers": {(DOMAIN, unique_id)},
            "name": "Garmin Connect",
            "manufacturer": "Garmin Connect",
        }

    async def async_update(self):
        """Update the data from Garmin Connect."""
        if not self.enabled:
            return

        await self._data.async_update()
        data = self._data.data
        if not data:
            self._attr_extra_state_attributes = {}
            _LOGGER.error("Didn't receive data from Garmin Connect")
            return
        self._attr_extra_state_attributes = {
            "source": self._data.data["source"],
            "last_synced": self._data.data["lastSyncTimestampGMT"],
            ATTR_ATTRIBUTION: ATTRIBUTION,
        }
        if self._type == "nextAlarm":
            self._attr_extra_state_attributes[
                "next_alarms"
            ] = calculate_next_active_alarms(self._data.data[self._type])
        if data.get(self._type) is None:
            _LOGGER.debug("Entity type %s not set in fetched data", self._type)
            self._attr_available = False
            return
        self._attr_available = True

        if "Duration" in self._type or "Seconds" in self._type:
            self._attr_state = data[self._type] // 60
        elif "Mass" in self._type or self._type == "weight":
            self._attr_state = round((data[self._type] / 1000), 2)
        elif (
            self._type == "bodyFat" or self._type == "bodyWater" or self._type == "bmi"
        ):
            self._attr_state = round(data[self._type], 2)
        elif self._type == "nextAlarm":
            active_alarms = calculate_next_active_alarms(data[self._type])
            if active_alarms:
                self._attr_state = active_alarms[0]
            else:
                self._attr_available = False
        else:
            self._attr_state = data[self._type]

        _LOGGER.debug(
            "Entity %s set to state %s %s",
            self._type,
            self.state,
            self.unit_of_measurement,
        )

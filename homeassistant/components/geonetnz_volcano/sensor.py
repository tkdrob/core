"""Feed Entity Manager Sensor support for GeoNet NZ Volcano Feeds."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import (
    ATTR_ATTRIBUTION,
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    CONF_UNIT_SYSTEM_IMPERIAL,
    LENGTH_KILOMETERS,
)
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.util import dt
from homeassistant.util.unit_system import IMPERIAL_SYSTEM

from .const import (
    ATTR_ACTIVITY,
    ATTR_DISTANCE,
    ATTR_EXTERNAL_ID,
    ATTR_HAZARDS,
    DEFAULT_ICON,
    DOMAIN,
    FEED,
)

_LOGGER = logging.getLogger(__name__)

ATTR_LAST_UPDATE = "feed_last_update"
ATTR_LAST_UPDATE_SUCCESSFUL = "feed_last_update_successful"


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the GeoNet NZ Volcano Feed platform."""
    manager = hass.data[DOMAIN][FEED][entry.entry_id]

    @callback
    def async_add_sensor(feed_manager, external_id, unit_system):
        """Add sensor entity from feed."""
        new_entity = GeonetnzVolcanoSensor(
            entry.entry_id, feed_manager, external_id, unit_system
        )
        _LOGGER.debug("Adding sensor %s", new_entity)
        async_add_entities([new_entity], True)

    manager.listeners.append(
        async_dispatcher_connect(
            hass, manager.async_event_new_entity(), async_add_sensor
        )
    )
    hass.async_create_task(manager.async_update())
    _LOGGER.debug("Sensor setup done")


class GeonetnzVolcanoSensor(SensorEntity):
    """This represents an external event with GeoNet NZ Volcano feed data."""

    _attr_icon = DEFAULT_ICON
    _attr_should_poll = False
    _attr_unit_of_measurement = "alert level"

    def __init__(self, config_entry_id, feed_manager, external_id, unit_system):
        """Initialize entity with data from feed entry."""
        self._config_entry_id = config_entry_id
        self._feed_manager = feed_manager
        self._external_id = external_id
        self._unit_system = unit_system
        self._remove_signal_update = None

    async def async_added_to_hass(self):
        """Call when entity is added to hass."""
        self._remove_signal_update = async_dispatcher_connect(
            self.hass,
            f"geonetnz_volcano_update_{self._external_id}",
            self._update_callback,
        )

    async def async_will_remove_from_hass(self) -> None:
        """Call when entity will be removed from hass."""
        if self._remove_signal_update:
            self._remove_signal_update()

    @callback
    def _update_callback(self):
        """Call update method."""
        self.async_schedule_update_ha_state(True)

    async def async_update(self):
        """Update this entity from the data held in the feed manager."""
        _LOGGER.debug("Updating %s", self._external_id)
        feed_entry = self._feed_manager.get_entry(self._external_id)
        last_update = self._feed_manager.last_update()
        last_update_successful = self._feed_manager.last_update_successful()
        if feed_entry:
            self._update_from_feed(feed_entry, last_update, last_update_successful)

    def _update_from_feed(self, feed_entry, last_update, last_update_successful):
        """Update the internal state from the provided feed entry."""
        self._attr_name = f"Volcano {feed_entry.title}"
        # Convert distance if not metric system.
        if self._unit_system == CONF_UNIT_SYSTEM_IMPERIAL:
            distance = round(
                IMPERIAL_SYSTEM.length(feed_entry.distance_to_home, LENGTH_KILOMETERS),
                1,
            )
        else:
            distance = round(feed_entry.distance_to_home, 1)
        self._attr_state = feed_entry.alert_level
        self._attr_extra_state_attributes = {}
        for key, value in (
            (ATTR_EXTERNAL_ID, self._external_id),
            (ATTR_ATTRIBUTION, feed_entry.attribution),
            (ATTR_ACTIVITY, feed_entry.activity),
            (ATTR_HAZARDS, feed_entry.hazards),
            (ATTR_LONGITUDE, round(feed_entry.coordinates[1], 5)),
            (ATTR_LATITUDE, round(feed_entry.coordinates[0], 5)),
            (ATTR_DISTANCE, distance),
            (ATTR_LAST_UPDATE, dt.as_utc(last_update) if last_update else None),
            (
                ATTR_LAST_UPDATE_SUCCESSFUL,
                dt.as_utc(last_update_successful) if last_update_successful else None,
            ),
        ):
            if value or isinstance(value, bool):
                self._attr_extra_state_attributes[key] = value

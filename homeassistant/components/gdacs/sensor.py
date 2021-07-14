"""Feed Entity Manager Sensor support for GDACS Feed."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.util import dt

from .const import DEFAULT_ICON, DOMAIN, FEED

_LOGGER = logging.getLogger(__name__)

ATTR_STATUS = "status"
ATTR_LAST_UPDATE = "last_update"
ATTR_LAST_UPDATE_SUCCESSFUL = "last_update_successful"
ATTR_LAST_TIMESTAMP = "last_timestamp"
ATTR_CREATED = "created"
ATTR_UPDATED = "updated"
ATTR_REMOVED = "removed"

DEFAULT_UNIT_OF_MEASUREMENT = "alerts"

# An update of this entity is not making a web request, but uses internal data only.
PARALLEL_UPDATES = 0


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the GDACS Feed platform."""
    manager = hass.data[DOMAIN][FEED][entry.entry_id]
    sensor = GdacsSensor(entry.entry_id, entry.unique_id, entry.title, manager)
    async_add_entities([sensor])
    _LOGGER.debug("Sensor setup done")


class GdacsSensor(SensorEntity):
    """This is a status sensor for the GDACS integration."""

    _attr_icon = DEFAULT_ICON
    _attr_should_poll = False
    _attr_unit_of_measurement = DEFAULT_UNIT_OF_MEASUREMENT

    def __init__(self, config_entry_id, config_unique_id, config_title, manager):
        """Initialize entity."""
        self._config_entry_id = config_entry_id
        self._attr_name = f"GDACS ({config_title})"
        self._attr_unique_id = config_unique_id
        self._manager = manager
        self._remove_signal_status = None

    async def async_added_to_hass(self):
        """Call when entity is added to hass."""
        self._remove_signal_status = async_dispatcher_connect(
            self.hass,
            f"gdacs_status_{self._config_entry_id}",
            self._update_status_callback,
        )
        _LOGGER.debug("Waiting for updates %s", self._config_entry_id)
        # First update is manual because of how the feed entity manager is updated.
        await self.async_update()

    async def async_will_remove_from_hass(self) -> None:
        """Call when entity will be removed from hass."""
        if self._remove_signal_status:
            self._remove_signal_status()

    @callback
    def _update_status_callback(self):
        """Call status update method."""
        _LOGGER.debug("Received status update for %s", self._config_entry_id)
        self.async_schedule_update_ha_state(True)

    async def async_update(self):
        """Update this entity from the data held in the feed manager."""
        _LOGGER.debug("Updating %s", self._config_entry_id)
        if self._manager:
            status_info = self._manager.status_info()
            if status_info:
                self._update_from_status_info(status_info)

    def _update_from_status_info(self, status_info):
        """Update the internal state from the provided information."""
        last_update = (
            dt.as_utc(status_info.last_update) if status_info.last_update else None
        )
        last_update_successful = None
        if status_info.last_update_successful:
            last_update_successful = dt.as_utc(status_info.last_update_successful)
        self._attr_state = status_info.total
        self._attr_extra_state_attributes = {}
        for key, value in (
            (ATTR_STATUS, status_info.status),
            (ATTR_LAST_UPDATE, last_update),
            (ATTR_LAST_UPDATE_SUCCESSFUL, last_update_successful),
            (ATTR_LAST_TIMESTAMP, status_info.last_timestamp),
            (ATTR_CREATED, status_info.created),
            (ATTR_UPDATED, status_info.updated),
            (ATTR_REMOVED, status_info.removed),
        ):
            if value or isinstance(value, bool):
                self._attr_extra_state_attributes[key] = value

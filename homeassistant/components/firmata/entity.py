"""Entity for Firmata devices."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import Entity

from .board import FirmataPinType
from .const import DOMAIN, FIRMATA_MANUFACTURER
from .pin import FirmataBoardPin


class FirmataEntity(Entity):
    """Representation of a Firmata entity."""

    def __init__(self, api):
        """Initialize the entity."""
        self._api = api
        self._attr_device_info = {
            "connections": {},
            "identifiers": {(DOMAIN, api.board.name)},
            "manufacturer": FIRMATA_MANUFACTURER,
            "name": api.board.name,
            "sw_version": api.board.firmware_version,
        }


class FirmataPinEntity(FirmataEntity):
    """Representation of a Firmata pin entity."""

    _attr_should_poll = False

    def __init__(
        self,
        api: type[FirmataBoardPin],
        config_entry: ConfigEntry,
        name: str,
        pin: FirmataPinType,
    ) -> None:
        """Initialize the pin entity."""
        super().__init__(api)
        self._attr_name = name
        location = (config_entry.entry_id, "pin", pin)
        self._attr_unique_id = "_".join(str(i) for i in location)

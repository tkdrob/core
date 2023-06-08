"""Entity representing a Google Sheets entit."""
from __future__ import annotations

from homeassistant.helpers.config_entry_oauth2_flow import OAuth2Session
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo, Entity, EntityDescription

from .const import DEFAULT_NAME, DOMAIN, MANUFACTURER


class GoogleSheetsEntity(Entity):
    """An HA implementation for Google Sheets entity."""

    _attr_has_entity_name = True

    def __init__(
        self,
        session: OAuth2Session,
        description: EntityDescription,
    ) -> None:
        """Initialize a Google Sheets entity."""
        self.session = session
        self.entity_description = description
        self._attr_unique_id = f"{session.config_entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, session.config_entry.entry_id)},
            manufacturer=MANUFACTURER,
            name=DEFAULT_NAME,
        )

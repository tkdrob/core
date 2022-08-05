"""Entity representing a Slack instance."""
from __future__ import annotations

from slack import WebClient

from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import DeviceInfo, EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_NAME, DOMAIN
from .coordinator import SlackDataUpdateCoordinator


class SlackEntity(CoordinatorEntity[SlackDataUpdateCoordinator]):
    """Representation of a Slack entity."""

    _attr_attribution = "Data provided by Slack"
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SlackDataUpdateCoordinator,
        description: EntityDescription | None,
    ) -> None:
        """Initialize a Slack entity."""
        super().__init__(coordinator)
        if description:
            self.entity_description = description
            _key = description.key
        elif self.name:
            _key = self.name.replace(" ", "_").lower()
        self._attr_unique_id = f"{coordinator.user_id}_{_key}"
        self._attr_device_info = DeviceInfo(
            configuration_url=coordinator.url,
            entry_type=dr.DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            manufacturer=DEFAULT_NAME,
            name=coordinator.config_entry.title,
        )

    @property
    def _client(self) -> WebClient:
        """Return client from the coordinator."""
        return self.coordinator.client

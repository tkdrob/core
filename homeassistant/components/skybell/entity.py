"""Entity representing a Skybell HD Doorbell."""

from __future__ import annotations

from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api.device import SkybellDevice
from .const import DEFAULT_NAME, DOMAIN
from .coordinator import SkybellDataUpdateCoordinator


class SkybellEntity(CoordinatorEntity[SkybellDataUpdateCoordinator]):
    """An HA implementation for Skybell entity."""

    _attr_attribution = "Data provided by Skybell.com"
    _attr_has_entity_name = True

    def __init__(
        self, coordinator: SkybellDataUpdateCoordinator, description: EntityDescription
    ) -> None:
        """Initialize a SkyBell entity."""
        super().__init__(coordinator)
        self.entity_description = description
        info = self._device.info
        self._attr_unique_id = f"{info.device_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, info.device_id)},
            connections={
                (
                    dr.CONNECTION_NETWORK_MAC,
                    info.device_settings.MAC_address,
                )
            },
            manufacturer=DEFAULT_NAME,
            model=info.device_settings.model_rev,
            name=info.name.capitalize(),
            sw_version=info.firmware,
        )

    @property
    def _device(self) -> SkybellDevice:
        """Return the device."""
        return self.coordinator.device

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        self._handle_coordinator_update()

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available and self._device.info.telemetry is not None

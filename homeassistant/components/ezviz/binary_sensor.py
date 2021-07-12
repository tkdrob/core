"""Support for Ezviz binary sensors."""
import logging

from pyezviz.constants import BinarySensorType

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_COORDINATOR, DOMAIN, MANUFACTURER
from .coordinator import EzvizDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up Ezviz sensors based on a config entry."""
    coordinator: EzvizDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    sensors = []

    for idx, camera in enumerate(coordinator.data):
        for name in camera:
            # Only add sensor with value.
            if camera.get(name) is None:
                continue

            if name in BinarySensorType.__members__:
                sensor_type_name = getattr(BinarySensorType, name).value
                sensors.append(
                    EzvizBinarySensor(coordinator, idx, name, sensor_type_name)
                )

    async_add_entities(sensors)


class EzvizBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a Ezviz sensor."""

    coordinator: EzvizDataUpdateCoordinator

    def __init__(
        self,
        coordinator: EzvizDataUpdateCoordinator,
        idx: int,
        name: str,
        sensor_type_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._idx = idx
        self._attr_name = name
        sensor_name = f"{coordinator.data[idx]['name']}.{name}"
        self._attr_device_class = sensor_type_name
        self._serial = coordinator.data[idx]["serial"]
        self._attr_unique_id = f"{self._serial}_{sensor_name}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._serial)},
            "name": coordinator.data[idx]["name"],
            "model": coordinator.data[idx]["device_sub_category"],
            "manufacturer": MANUFACTURER,
            "sw_version": coordinator.data[idx]["version"],
        }

    @property
    def is_on(self) -> bool:
        """Return the state of the sensor."""
        return self.coordinator.data[self._idx][self.name]

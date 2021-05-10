"""The DoorBird integration base entity."""

from homeassistant.const import (
    ATTR_MANUFACTURER,
    ATTR_MODEL,
    ATTR_NAME,
    ATTR_SW_VERSION,
)
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import Entity

from .const import (
    DOORBIRD_INFO_KEY_BUILD_NUMBER,
    DOORBIRD_INFO_KEY_DEVICE_TYPE,
    DOORBIRD_INFO_KEY_FIRMWARE,
    MANUFACTURER,
)
from .util import get_mac_address_from_doorstation_info


class DoorBirdEntity(Entity):
    """Base class for doorbird entities."""

    def __init__(self, doorstation, doorstation_info):
        """Initialize the entity."""
        super().__init__()
        self._doorstation_info = doorstation_info
        self._doorstation = doorstation
        self._mac_addr = get_mac_address_from_doorstation_info(doorstation_info)

    @property
    def device_info(self):
        """Doorbird device info."""
        firmware = self._doorstation_info[DOORBIRD_INFO_KEY_FIRMWARE]
        firmware_build = self._doorstation_info[DOORBIRD_INFO_KEY_BUILD_NUMBER]
        return {
            "connections": {(dr.CONNECTION_NETWORK_MAC, self._mac_addr)},
            ATTR_NAME: self._doorstation.name,
            ATTR_MANUFACTURER: MANUFACTURER,
            ATTR_SW_VERSION: f"{firmware} {firmware_build}",
            ATTR_MODEL: self._doorstation_info[DOORBIRD_INFO_KEY_DEVICE_TYPE],
        }

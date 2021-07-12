"""Support for Fibaro locks."""
from homeassistant.components.lock import DOMAIN, LockEntity

from . import FIBARO_DEVICES, FibaroDevice


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Fibaro locks."""
    if discovery_info is None:
        return

    add_entities(
        [FibaroLock(device) for device in hass.data[FIBARO_DEVICES]["lock"]], True
    )


class FibaroLock(FibaroDevice, LockEntity):
    """Representation of a Fibaro Lock."""

    def __init__(self, fibaro_device):
        """Initialize the Fibaro device."""
        super().__init__(fibaro_device)
        self.entity_id = f"{DOMAIN}.{self.ha_id}"

    def lock(self, **kwargs):
        """Lock the device."""
        self.action("secure")
        self._attr_is_locked = True

    def unlock(self, **kwargs):
        """Unlock the device."""
        self.action("unsecure")
        self._attr_is_locked = False

    def update(self):
        """Update device state."""
        self._attr_is_locked = self.current_binary_state

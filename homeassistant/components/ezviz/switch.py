"""Support for Ezviz Switch sensors."""
import logging

from pyezviz.constants import DeviceSwitchType

from homeassistant.components.switch import DEVICE_CLASS_SWITCH, SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DATA_COORDINATOR, DOMAIN, MANUFACTURER

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Ezviz switch based on a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    switch_entities = []
    supported_switches = []

    for switches in DeviceSwitchType:
        supported_switches.append(switches.value)

    supported_switches = set(supported_switches)

    for idx, camera in enumerate(coordinator.data):
        if not camera.get("switches"):
            continue
        for switch in camera["switches"]:
            if switch not in supported_switches:
                continue
            switch_entities.append(EzvizSwitch(coordinator, idx, switch))

    async_add_entities(switch_entities)


class EzvizSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a Ezviz sensor."""

    _attr_device_class = DEVICE_CLASS_SWITCH

    def __init__(self, coordinator, idx, switch):
        """Initialize the switch."""
        super().__init__(coordinator)
        self._idx = idx
        self.switch = switch
        self._serial = coordinator.data[idx]["serial"]
        self._attr_name = (
            f"{coordinator.data[idx]['name']}.{DeviceSwitchType(switch).name}"
        )
        self._attr_unique_id = f"{coordinator.data[idx]['seria']}_{self.name}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.data[idx]["serial"])},
            "name": coordinator.data[idx]["name"],
            "model": coordinator.data[idx]["device_sub_category"],
            "manufacturer": MANUFACTURER,
            "sw_version": coordinator.data[idx]["version"],
        }

    @property
    def is_on(self):
        """Return the state of the switch."""
        return self.coordinator.data[self._idx]["switches"][self.switch]

    def turn_on(self, **kwargs):
        """Change a device switch on the camera."""
        _LOGGER.debug("Set EZVIZ Switch '%s' to on", self.switch)

        self.coordinator.ezviz_client.switch_status(self._serial, self.switch, 1)

    def turn_off(self, **kwargs):
        """Change a device switch on the camera."""
        _LOGGER.debug("Set EZVIZ Switch '%s' to off", self.switch)

        self.coordinator.ezviz_client.switch_status(self._serial, self.switch, 0)

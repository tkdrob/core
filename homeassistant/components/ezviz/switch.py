"""Support for Ezviz Switch sensors."""
import logging

from pyezviz.constants import DeviceSwitchType

from homeassistant.components.switch import DEVICE_CLASS_SWITCH, SwitchEntity
from homeassistant.const import (
    ATTR_IDENTIFIERS,
    ATTR_MANUFACTURER,
    ATTR_MODEL,
    ATTR_NAME,
    ATTR_SW_VERSION,
)
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

    def __init__(self, coordinator, idx, switch):
        """Initialize the switch."""
        super().__init__(coordinator)
        self._idx = idx
        self._camera_name = self.coordinator.data[self._idx]["name"]
        self._name = switch
        self._sensor_name = f"{self._camera_name}.{DeviceSwitchType(self._name).name}"
        self._serial = self.coordinator.data[self._idx]["serial"]
        self._device_class = DEVICE_CLASS_SWITCH

    @property
    def name(self):
        """Return the name of the Ezviz switch."""
        return f"{self._camera_name}.{DeviceSwitchType(self._name).name}"

    @property
    def is_on(self):
        """Return the state of the switch."""
        return self.coordinator.data[self._idx]["switches"][self._name]

    @property
    def unique_id(self):
        """Return the unique ID of this switch."""
        return f"{self._serial}_{self._sensor_name}"

    def turn_on(self, **kwargs):
        """Change a device switch on the camera."""
        _LOGGER.debug("Set EZVIZ Switch '%s' to on", self._name)

        self.coordinator.ezviz_client.switch_status(self._serial, self._name, 1)

    def turn_off(self, **kwargs):
        """Change a device switch on the camera."""
        _LOGGER.debug("Set EZVIZ Switch '%s' to off", self._name)

        self.coordinator.ezviz_client.switch_status(self._serial, self._name, 0)

    @property
    def device_info(self):
        """Return the device_info of the device."""
        return {
            ATTR_IDENTIFIERS: {(DOMAIN, self._serial)},
            ATTR_NAME: self.coordinator.data[self._idx]["name"],
            ATTR_MODEL: self.coordinator.data[self._idx]["device_sub_category"],
            ATTR_MANUFACTURER: MANUFACTURER,
            ATTR_SW_VERSION: self.coordinator.data[self._idx]["version"],
        }

    @property
    def device_class(self):
        """Device class for the sensor."""
        return self._device_class

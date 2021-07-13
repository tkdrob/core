"""AVM FRITZ!Box connectivity sensor."""
import logging

from fritzconnection.core.exceptions import FritzConnectionException

from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_CONNECTIVITY,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .common import FritzBoxBaseEntity, FritzBoxTools
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up entry."""
    _LOGGER.debug("Setting up FRITZ!Box binary sensors")
    fritzbox_tools: FritzBoxTools = hass.data[DOMAIN][entry.entry_id]

    if fritzbox_tools.connection and "WANIPConn1" in fritzbox_tools.connection.services:
        # Only routers are supported at the moment
        async_add_entities(
            [FritzBoxConnectivitySensor(fritzbox_tools, entry.title)], True
        )


class FritzBoxConnectivitySensor(FritzBoxBaseEntity, BinarySensorEntity):
    """Define FRITZ!Box connectivity class."""

    _attr_device_class = DEVICE_CLASS_CONNECTIVITY

    def __init__(
        self, fritzbox_tools: FritzBoxTools, device_friendly_name: str
    ) -> None:
        """Init FRITZ!Box connectivity class."""
        self._attr_unique_id = f"{fritzbox_tools.unique_id}-connectivity"
        self._attr_name = f"{device_friendly_name} Connectivity"
        self._attr_is_on = True
        self._attr_available = True
        super().__init__(fritzbox_tools, device_friendly_name)

    def update(self) -> None:
        """Update data."""
        _LOGGER.debug("Updating FRITZ!Box binary sensors")
        self._attr_is_on = True
        try:
            if (
                self._fritzbox_tools.connection
                and "WANCommonInterfaceConfig1"
                in self._fritzbox_tools.connection.services
            ):
                link_props = self._fritzbox_tools.connection.call_action(
                    "WANCommonInterfaceConfig1", "GetCommonLinkProperties"
                )
                is_up = link_props["NewPhysicalLinkStatus"]
                self._attr_is_on = is_up == "Up"
            else:
                if self._fritzbox_tools.fritz_status:
                    self._attr_is_on = self._fritzbox_tools.fritz_status.is_connected

            self._attr_available = True

        except FritzConnectionException:
            _LOGGER.error("Error getting the state from the FRITZ!Box", exc_info=True)
            self._attr_available = False

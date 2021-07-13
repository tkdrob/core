"""Support for Freebox Delta, Revolution and Mini 4K."""
from __future__ import annotations

import logging

from freebox_api.exceptions import InsufficientPermissionsError

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .router import FreeboxRouter

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up the switch."""
    router = hass.data[DOMAIN][entry.unique_id]
    async_add_entities([FreeboxWifiSwitch(router)], True)


class FreeboxWifiSwitch(SwitchEntity):
    """Representation of a freebox wifi switch."""

    _attr_name = "Freebox WiFi"

    def __init__(self, router: FreeboxRouter) -> None:
        """Initialize the Wifi switch."""
        self._router = router
        self._attr_unique_id = f"{router.mac} {self.name}"

    async def _async_set_state(self, enabled: bool):
        """Turn the switch on or off."""
        wifi_config = {"enabled": enabled}
        try:
            await self._router.wifi.set_global_config(wifi_config)
        except InsufficientPermissionsError:
            _LOGGER.warning(
                "Home Assistant does not have permissions to modify the Freebox settings. Please refer to documentation"
            )

    async def async_turn_on(self, **kwargs):
        """Turn the switch on."""
        await self._async_set_state(True)

    async def async_turn_off(self, **kwargs):
        """Turn the switch off."""
        await self._async_set_state(False)

    async def async_update(self):
        """Get the state and update it."""
        datas = await self._router.wifi.get_global_config()
        active = datas["enabled"]
        self._attr_is_on = bool(active)
        self._attr_device_info = self._router.device_info

"""Support for Google Sheets Sensors."""
from __future__ import annotations

from datetime import datetime, timedelta
import time

import aiohttp

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_call_later

from .const import DOMAIN
from .entity import GoogleSheetsEntity

SCAN_INTERVAL = timedelta(hours=1)

SENSOR_TYPE = SensorEntityDescription(
    key="access_token",
    name="Access token",
    icon="mdi:account-key",
    entity_registry_enabled_default=False,
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Google Mail sensor."""
    async_add_entities(
        [GoogleSheetsSensor(hass.data[DOMAIN][entry.entry_id], SENSOR_TYPE)], True
    )


class GoogleSheetsSensor(GoogleSheetsEntity, SensorEntity):
    """Representation of a Google Sheets sensor."""

    _attr_should_poll = False

    async def async_added_to_hass(self) -> None:
        """Handle when an entity is about to be added to Home Assistant."""
        await self._async_call_loop()

    async def _async_call_loop(self, now: datetime | None = None) -> None:
        try:
            await self.session.async_ensure_token_valid()
        except aiohttp.ClientResponseError as ex:
            if 400 <= ex.status < 500:
                raise ConfigEntryAuthFailed(
                    "OAuth session is not valid, reauth required"
                ) from ex
            raise HomeAssistantError from ex
        except aiohttp.ClientError as ex:
            raise HomeAssistantError from ex
        self.async_write_ha_state()
        self._attr_native_value = self.session.token[CONF_ACCESS_TOKEN]
        async_call_later(
            self.hass,
            self.session.token["expires_at"] - time.time(),
            self._async_call_loop,
        )

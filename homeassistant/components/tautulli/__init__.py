"""The Tautulli integration."""
from __future__ import annotations

import logging

from pytautulli import Tautulli, exceptions

from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import (
    ATTR_IDENTIFIERS,
    ATTR_MANUFACTURER,
    ATTR_NAME,
    CONF_API_KEY,
    CONF_HOST,
    CONF_PATH,
    CONF_PORT,
    CONF_SSL,
    CONF_VERIFY_SSL,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    CONF_MONITORED_USERS,
    DATA_KEY_API,
    DATA_KEY_COORDINATOR,
    DEFAULT_NAME,
    DEFAULT_PATH,
    DEFAULT_PORT,
    DEFAULT_SSL,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
    MIN_TIME_BETWEEN_UPDATES,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


async def async_setup(hass: HomeAssistant, config):
    """Set up the Tautulli component."""
    if SENSOR_DOMAIN in config:
        for entry in config[SENSOR_DOMAIN]:
            if entry["platform"] == DOMAIN:
                if CONF_PORT not in entry:
                    entry[CONF_PORT] = DEFAULT_PORT
                if CONF_PATH not in entry:
                    entry[CONF_PATH] = DEFAULT_PATH
                if CONF_VERIFY_SSL not in entry:
                    entry[CONF_VERIFY_SSL] = DEFAULT_VERIFY_SSL
                if CONF_SSL not in entry:
                    entry[CONF_SSL] = DEFAULT_SSL
                hass.async_create_task(
                    hass.config_entries.flow.async_init(
                        DOMAIN, context={"source": SOURCE_IMPORT}, data=entry
                    )
                )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Tautulli from a config entry."""
    api = Tautulli(
        host=entry.data[CONF_HOST],
        port=entry.data[CONF_PORT],
        path=entry.data[CONF_PATH],
        api_key=entry.data[CONF_API_KEY],
        loop=hass.loop,
        session=async_get_clientsession(hass, entry.data[CONF_VERIFY_SSL]),
        ssl=entry.data[CONF_SSL],
    )
    if not entry.options:
        await api.get_users()
        options = dict(entry.options)
        options.setdefault(DOMAIN, {})
        options[CONF_MONITORED_USERS] = api.tautulli_users
        hass.config_entries.async_update_entry(entry, options=options)

    try:
        await api.test_connection()
        await api.get_data()
    except exceptions.ConnectError as ex:
        _LOGGER.warning("Failed to connect: %s", ex)
        raise ConfigEntryNotReady from ex

    async def async_update_data():
        """Fetch data from API endpoint."""
        try:
            await api.get_data()
            hass.data[DOMAIN][entry.entry_id][DATA_KEY_API] = api
        except exceptions.ConnectError as err:
            raise UpdateFailed(f"Failed to communicate with device {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DEFAULT_NAME,
        update_method=async_update_data,
        update_interval=MIN_TIME_BETWEEN_UPDATES,
    )
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        DATA_KEY_API: api,
        DATA_KEY_COORDINATOR: coordinator,
    }

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class TautulliEntity(CoordinatorEntity):
    """Defines a base Tautulli entity."""

    def __init__(
        self,
        api,
        coordinator,
        name,
        server_unique_id,
    ) -> None:
        """Initialize the Tautulli entity."""
        super().__init__(coordinator)
        self.api = api
        self._server_unique_id = server_unique_id
        self._icon = None
        self._name = name

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return self._name

    @property
    def icon(self):
        """Return the mdi icon of the entity."""
        return self._icon

    @property
    def device_info(self) -> DeviceInfo | None:
        """Return device information about the application."""
        return {
            ATTR_IDENTIFIERS: {(DOMAIN, self._server_unique_id)},
            ATTR_NAME: "Activity Sensor",
            ATTR_MANUFACTURER: DEFAULT_NAME,
            "entry_type": "service",
        }

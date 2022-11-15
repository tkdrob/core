"""Support for Google Mail Sensors."""
from __future__ import annotations

from datetime import timedelta, datetime, timezone
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_TOKEN
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials

import voluptuous as vol
from googleapiclient.discovery import build
from homeassistant.helpers.config_entry_oauth2_flow import OAuth2Session
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.service import async_extract_config_entry_ids

from .const import (
    ATTR_ENABLED,
    ATTR_END,
    ATTR_MESSAGE,
    ATTR_PLAIN_TEXT,
    ATTR_RESTRICT_CONTACTS,
    ATTR_RESTRICT_DOMAIN,
    ATTR_START,
    ATTR_TITLE,
    DATA_CONFIG_ENTRY,
    DEFAULT_ACCESS,
    DOMAIN,
    #FeatureAccess,
)
from .entity import GoogleMailEntity

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(hours=1)

SERVICE_SET_VACATION = "set_vacation"

SERVICE_SCHEMA = vol.All(
    cv.make_entity_service_schema(
        {
            vol.Optional(ATTR_TITLE): cv.string,
            vol.Required(ATTR_MESSAGE): cv.string,
            vol.Optional(ATTR_PLAIN_TEXT, default=True): cv.boolean,
            vol.Required(ATTR_ENABLED, default=True): cv.boolean,
            vol.Required(ATTR_RESTRICT_CONTACTS, default=True): cv.boolean,
            vol.Required(ATTR_RESTRICT_DOMAIN, default=True): cv.boolean,
            vol.Optional(ATTR_START): cv.date,
            vol.Optional(ATTR_END): cv.date,
        },
    )
)

SENSOR_TYPE = SensorEntityDescription(
    key="vacation_end_date",
    name="Vacation end date",
    icon="mdi:clock",
    device_class=SensorDeviceClass.TIMESTAMP,
)


async def async_setup_service(hass: HomeAssistant) -> None:
    """Add the services for Google Mail."""

    async def extract_gmail_config_entries(call: ServiceCall) -> list[ConfigEntry]:
        return [
            entry
            for entry_id in await async_extract_config_entry_ids(hass, call)
            if (entry := hass.config_entries.async_get_entry(entry_id))
            and entry.domain == DOMAIN
        ]

    def _set_vacation(call: ServiceCall, entry: ConfigEntry) -> None:
        """Run vacation call in the executor."""
        credentials = Credentials(entry.data[CONF_TOKEN][CONF_ACCESS_TOKEN])
        service = build("gmail", "v1", credentials=credentials)
        settings = {
            "enableAutoReply": call.data[ATTR_ENABLED],
            "responseSubject": call.data.get(ATTR_TITLE),
            "restrictToContacts": call.data[ATTR_RESTRICT_CONTACTS],
            "restrictToDomain": call.data[ATTR_RESTRICT_DOMAIN],
        }
        if _date := call.data.get(ATTR_START):
            _dt = datetime.combine(_date, datetime.min.time())
            settings["startTime"] = _dt.timestamp() * 1000
        if _date := call.data.get(ATTR_END):
            _dt = datetime.combine(_date, datetime.min.time())
            settings["endTime"] = _dt.timestamp() * 1000
        if call.data[ATTR_PLAIN_TEXT]:
            settings["responseBodyPlainText"] = call.data[ATTR_MESSAGE]
        else:
            settings["responseBodyHtml"] = call.data[ATTR_MESSAGE]
        # add to docs https://console.cloud.google.com/apis/library/gmail.googleapis.com?project=home-assistant-17698
        _settings = service.users().settings()
        try:
            _settings.updateVacation(userId="me", body=settings).execute()
        except RefreshError as ex:
            entry.async_start_reauth(hass)
            raise ex 

    async def set_vacation(call: ServiceCall) -> None: #TODO throw error if not all targets are valid
        """Set vacation responder settings for Google Mail."""
        _LOGGER.warning(call.data)
        if not (entries := await extract_gmail_config_entries(call)):
            raise HomeAssistantError(
                f"Failed to call service '{SERVICE_SET_VACATION}'. Config entry for target not found"
            )
        for entry in entries:
            #if not entry:
            #    raise ValueError(f"Invalid config entry: {call.data[DATA_CONFIG_ENTRY]}")
            if not (session := hass.data[DOMAIN].get(entry.entry_id)):
                raise ValueError(f"Config entry not loaded: {call.data[DATA_CONFIG_ENTRY]}")
            await session.async_ensure_token_valid()
            await hass.async_add_executor_job(_set_vacation, call, entry)

    hass.services.async_register(
        domain=DOMAIN,
        service=SERVICE_SET_VACATION,
        schema=SERVICE_SCHEMA,
        service_func=set_vacation,
    )


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Google Mail sensor."""
    async_add_entities([GoogleMailSensor(entry, SENSOR_TYPE)], True)

    await async_setup_service(hass)


class GoogleMailSensor(GoogleMailEntity, SensorEntity):
    """Representation of a Google Mail sensor."""

    async def async_update(self) -> None:
        """Get the vacation data."""
        session: OAuth2Session = self.hass.data[DOMAIN].get(self.entry.entry_id)
        await session.async_ensure_token_valid()

        def _getVacation() -> dict[str, Any]:
            """Get profile from inside the executor."""
            credentials = Credentials(self.entry.data[CONF_TOKEN][CONF_ACCESS_TOKEN])
            service = build("gmail", "v1", credentials=credentials)
            return service.users().settings().getVacation(userId="me").execute()

        try:
            data = await self.hass.async_add_executor_job(_getVacation)
        except RefreshError as ex:
            self.entry.async_start_reauth(self.hass)
            raise ex 

        if data["enableAutoReply"]:
            value = datetime.fromtimestamp(int(data["endTime"]) / 1000, tz=timezone.utc)
        else:
            value = None
        self._attr_native_value = value

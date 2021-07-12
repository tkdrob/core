"""Sensor platform for FireServiceRota integration."""
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DATA_CLIENT, DOMAIN as FIRESERVICEROTA_DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up FireServiceRota sensor based on a config entry."""
    client = hass.data[FIRESERVICEROTA_DOMAIN][entry.entry_id][DATA_CLIENT]

    async_add_entities([IncidentsSensor(client)])


class IncidentsSensor(RestoreEntity, SensorEntity):
    """Representation of FireServiceRota incidents sensor."""

    _attr_name = "Incidents"
    _attr_should_poll = False

    def __init__(self, client):
        """Initialize."""
        self._client = client
        self._entry_id = client.entry_id
        self._attr_unique_id = f"{client.unique_id}_Incidents"

    async def async_added_to_hass(self) -> None:
        """Run when about to be added to hass."""
        await super().async_added_to_hass()

        state = await self.async_get_last_state()
        if state:
            self._attr_state = state.state
            self._attr_extra_state_attributes = state.attributes
            if "id" in self.extra_state_attributes:
                self._client.incident_id = self.extra_state_attributes["id"]
            _LOGGER.debug("Restored entity 'Incidents' to: %s", self.state)

        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{FIRESERVICEROTA_DOMAIN}_{self._entry_id}_update",
                self.client_update,
            )
        )

    @callback
    def client_update(self) -> None:
        """Handle updated data from the data client."""
        data = self._client.websocket.incident_data
        if not data or "body" not in data:
            return

        self._attr_state = data["body"]
        self._attr_extra_state_attributes = data
        if "id" in self.extra_state_attributes:
            self._client.incident_id = self.extra_state_attributes["id"]
        self._attr_icon = "mdi:fire-truck"
        if (
            "prio" in self.extra_state_attributes
            and self.extra_state_attributes["prio"][0] == "a"
        ):
            self._attr_icon = "mdi:ambulance"
        attr = {}
        data = self.extra_state_attributes

        if not data:
            self._attr_extra_state_attributes = attr

        for value in (
            "id",
            "trigger",
            "created_at",
            "message_to_speech_url",
            "prio",
            "type",
            "responder_mode",
            "can_respond_until",
        ):
            if data.get(value):
                attr[value] = data[value]

            if "address" not in data:
                continue

            for address_value in (
                "latitude",
                "longitude",
                "address_type",
                "formatted_address",
            ):
                if address_value in data["address"]:
                    attr[address_value] = data["address"][address_value]

        self._attr_extra_state_attributes = attr
        self.async_write_ha_state()

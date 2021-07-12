"""Switch platform for FireServiceRota integration."""
import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DATA_CLIENT, DATA_COORDINATOR, DOMAIN as FIRESERVICEROTA_DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up FireServiceRota switch based on a config entry."""
    client = hass.data[FIRESERVICEROTA_DOMAIN][entry.entry_id][DATA_CLIENT]

    coordinator = hass.data[FIRESERVICEROTA_DOMAIN][entry.entry_id][DATA_COORDINATOR]

    async_add_entities([ResponseSwitch(coordinator, client, entry)])


class ResponseSwitch(SwitchEntity):
    """Representation of an FireServiceRota switch."""

    _attr_name = "Incident Response"
    _attr_should_poll = False

    def __init__(self, coordinator, client, entry):
        """Initialize."""
        self._coordinator = coordinator
        self._client = client
        self._attr_unique_id = f"{entry.unique_id}_Response"
        self._entry_id = entry.entry_id

    async def async_turn_on(self, **kwargs) -> None:
        """Send Acknowledge response status."""
        await self.async_set_response(True)

    async def async_turn_off(self, **kwargs) -> None:
        """Send Reject response status."""
        await self.async_set_response(False)

    async def async_set_response(self, value) -> None:
        """Send response status."""
        if not self._client.on_duty:
            _LOGGER.debug(
                "Cannot send incident response when not on duty",
            )
            return

        await self._client.async_set_response(value)
        self.client_update()

    async def async_added_to_hass(self) -> None:
        """Register update callback."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{FIRESERVICEROTA_DOMAIN}_{self._entry_id}_update",
                self.client_update,
            )
        )
        self.async_on_remove(
            self._coordinator.async_add_listener(self.async_write_ha_state)
        )

    @callback
    def client_update(self) -> None:
        """Handle updated incident data from the client."""
        self.async_schedule_update_ha_state(True)

    async def async_update(self) -> bool:
        """Update FireServiceRota response data."""
        data = await self._client.async_response_update()

        if not data or "status" not in data:
            return

        self._attr_is_on = data["status"] == "acknowledged"
        self._attr_available = self._client.on_duty
        self._attr_icon = "mdi:forum"
        if data["status"] == "acknowledged":
            self._attr_icon = "mdi:run-fast"
        if data["status"] == "rejected":
            self._attr_icon = "mdi:account-off-outline"
        if not data:
            self._attr_extra_state_attributes = {}
        else:
            self._attr_extra_state_attributes = {
                key: data[key]
                for key in (
                    "user_name",
                    "assigned_skill_ids",
                    "responded_at",
                    "start_time",
                    "status",
                    "reported_status",
                    "arrived_at_station",
                    "available_at_incident_creation",
                    "active_duty_function_ids",
                )
                if key in data
            }

        _LOGGER.debug("Set state of entity 'Response Switch' to '%s'", self.state)

"""Support for Yale Alarm."""
from __future__ import annotations

from homeassistant.components.alarm_control_panel import AlarmControlPanelEntity
from homeassistant.components.alarm_control_panel.const import (
    SUPPORT_ALARM_ARM_AWAY,
    SUPPORT_ALARM_ARM_HOME,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import COORDINATOR, DOMAIN, MANUFACTURER, MODEL, STATE_MAP
from .coordinator import YaleDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the alarm entry."""

    async_add_entities(
        [YaleAlarmDevice(coordinator=hass.data[DOMAIN][entry.entry_id][COORDINATOR])]
    )


class YaleAlarmDevice(CoordinatorEntity, AlarmControlPanelEntity):
    """Represent a Yale Smart Alarm."""

    def __init__(self, coordinator: YaleDataUpdateCoordinator) -> None:
        """Initialize the Yale Alarm Device."""
        super().__init__(coordinator)
        self._attr_name: str = coordinator.entry.data[CONF_NAME]
        self._attr_unique_id = coordinator.entry.entry_id
        self._identifier: str = coordinator.entry.data[CONF_USERNAME]

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._identifier)},
            manufacturer=MANUFACTURER,
            model=MODEL,
            name=str(self.name),
        )

    @property
    def state(self):
        """Return the state of the device."""
        return STATE_MAP.get(self.coordinator.data["alarm"])

    @property
    def available(self):
        """Return if entity is available."""
        return STATE_MAP.get(self.coordinator.data["alarm"]) is not None

    @property
    def code_arm_required(self):
        """Whether the code is required for arm actions."""
        return False

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        return SUPPORT_ALARM_ARM_HOME | SUPPORT_ALARM_ARM_AWAY

    def alarm_disarm(self, code=None):
        """Send disarm command."""
        self.coordinator.yale.disarm()

    def alarm_arm_home(self, code=None):
        """Send arm home command."""
        self.coordinator.yale.arm_partial()

    def alarm_arm_away(self, code=None):
        """Send arm away command."""
        self.coordinator.yale.arm_full()

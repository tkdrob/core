"""Support for Rheem EcoNet water heaters."""
import logging

from pyeconet.equipment import EquipmentType
from pyeconet.equipment.water_heater import WaterHeaterOperationMode

from homeassistant.components.water_heater import (
    ATTR_TEMPERATURE,
    STATE_ECO,
    STATE_ELECTRIC,
    STATE_GAS,
    STATE_HEAT_PUMP,
    STATE_HIGH_DEMAND,
    STATE_OFF,
    STATE_PERFORMANCE,
    SUPPORT_AWAY_MODE,
    SUPPORT_OPERATION_MODE,
    SUPPORT_TARGET_TEMPERATURE,
    WaterHeaterEntity,
)
from homeassistant.core import callback

from . import EcoNetEntity
from .const import DOMAIN, EQUIPMENT

_LOGGER = logging.getLogger(__name__)

ECONET_STATE_TO_HA = {
    WaterHeaterOperationMode.ENERGY_SAVING: STATE_ECO,
    WaterHeaterOperationMode.HIGH_DEMAND: STATE_HIGH_DEMAND,
    WaterHeaterOperationMode.OFF: STATE_OFF,
    WaterHeaterOperationMode.HEAT_PUMP_ONLY: STATE_HEAT_PUMP,
    WaterHeaterOperationMode.ELECTRIC_MODE: STATE_ELECTRIC,
    WaterHeaterOperationMode.GAS: STATE_GAS,
    WaterHeaterOperationMode.PERFORMANCE: STATE_PERFORMANCE,
}
HA_STATE_TO_ECONET = {value: key for key, value in ECONET_STATE_TO_HA.items()}

SUPPORT_FLAGS_HEATER = SUPPORT_TARGET_TEMPERATURE | SUPPORT_OPERATION_MODE


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up EcoNet water heater based on a config entry."""
    equipment = hass.data[DOMAIN][EQUIPMENT][entry.entry_id]
    async_add_entities(
        [
            EcoNetWaterHeater(water_heater)
            for water_heater in equipment[EquipmentType.WATER_HEATER]
        ],
        True,
    )


class EcoNetWaterHeater(EcoNetEntity, WaterHeaterEntity):
    """Define a Econet water heater."""

    def __init__(self, water_heater):
        """Initialize."""
        super().__init__(water_heater)
        self._running = water_heater.running
        self.water_heater = water_heater
        self.ha_state_to_econet = {}
        if water_heater.modes:
            self._attr_supported_features = SUPPORT_FLAGS_HEATER
        else:
            self._attr_supported_features = SUPPORT_TARGET_TEMPERATURE
        if water_heater.supports_away:
            self._attr_supported_features += SUPPORT_AWAY_MODE
        self._attr_operation_list = []
        for mode in water_heater.modes:
            if (
                mode is not WaterHeaterOperationMode.UNKNOWN
                and mode is not WaterHeaterOperationMode.VACATION
            ):
                self._attr_operation_list.append(ECONET_STATE_TO_HA[mode])
        self._attr_min_temp = water_heater.set_point_limits[0]
        self._attr_max_temp = water_heater.set_point_limits[1]

    @callback
    def on_update_received(self):
        """Update was pushed from the ecoent API."""
        if self._running != self.water_heater.running:
            # Water heater running state has changed so check usage on next update
            self._attr_should_poll = True
            self._running = self.water_heater.running
        self.async_write_ha_state()

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        target_temp = kwargs.get(ATTR_TEMPERATURE)
        if target_temp is not None:
            self.water_heater.set_set_point(target_temp)
        else:
            _LOGGER.error("A target temperature must be provided")

    def set_operation_mode(self, operation_mode):
        """Set operation mode."""
        op_mode_to_set = HA_STATE_TO_ECONET.get(operation_mode)
        if op_mode_to_set is not None:
            self.water_heater.set_mode(op_mode_to_set)
        else:
            _LOGGER.error("Invalid operation mode: %s", operation_mode)

    async def async_update(self):
        """Get the latest energy usage."""
        await self.water_heater.get_energy_usage()
        await self.water_heater.get_water_usage()
        self._attr_should_poll = False
        self._attr_target_temperature = self.water_heater.set_point
        self._attr_is_away_mode_on = self._econet.away
        self._attr_current_operation = STATE_OFF
        if self.water_heater.mode is not None:
            self._attr_current_operation = ECONET_STATE_TO_HA[self.water_heater.mode]
        self.async_write_ha_state()

    def turn_away_mode_on(self):
        """Turn away mode on."""
        self.water_heater.set_away_mode(True)

    def turn_away_mode_off(self):
        """Turn away mode off."""
        self.water_heater.set_away_mode(False)

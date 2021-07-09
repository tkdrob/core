"""Demo platform that offers a fake climate device."""
from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
    CURRENT_HVAC_COOL,
    CURRENT_HVAC_HEAT,
    HVAC_MODE_AUTO,
    HVAC_MODE_COOL,
    HVAC_MODE_HEAT,
    HVAC_MODE_HEAT_COOL,
    HVAC_MODE_OFF,
    HVAC_MODES,
    SUPPORT_AUX_HEAT,
    SUPPORT_FAN_MODE,
    SUPPORT_PRESET_MODE,
    SUPPORT_SWING_MODE,
    SUPPORT_TARGET_HUMIDITY,
    SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_TARGET_TEMPERATURE_RANGE,
)
from homeassistant.const import ATTR_TEMPERATURE, TEMP_CELSIUS, TEMP_FAHRENHEIT

from . import DOMAIN

SUPPORT_FLAGS = 0


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Demo climate devices."""
    async_add_entities(
        [
            DemoClimate(
                unique_id="climate_1",
                name="HeatPump",
                target_temperature=68,
                unit_of_measurement=TEMP_FAHRENHEIT,
                preset=None,
                current_temperature=77,
                fan_mode=None,
                target_humidity=None,
                current_humidity=None,
                swing_mode=None,
                hvac_mode=HVAC_MODE_HEAT,
                hvac_action=CURRENT_HVAC_HEAT,
                aux=None,
                target_temp_high=None,
                target_temp_low=None,
                hvac_modes=[HVAC_MODE_HEAT, HVAC_MODE_OFF],
            ),
            DemoClimate(
                unique_id="climate_2",
                name="Hvac",
                target_temperature=21,
                unit_of_measurement=TEMP_CELSIUS,
                preset=None,
                current_temperature=22,
                fan_mode="On High",
                target_humidity=67,
                current_humidity=54,
                swing_mode="Off",
                hvac_mode=HVAC_MODE_COOL,
                hvac_action=CURRENT_HVAC_COOL,
                aux=False,
                target_temp_high=None,
                target_temp_low=None,
                hvac_modes=[mode for mode in HVAC_MODES if mode != HVAC_MODE_HEAT_COOL],
            ),
            DemoClimate(
                unique_id="climate_3",
                name="Ecobee",
                target_temperature=None,
                unit_of_measurement=TEMP_CELSIUS,
                preset="home",
                preset_modes=["home", "eco"],
                current_temperature=23,
                fan_mode="Auto Low",
                target_humidity=None,
                current_humidity=None,
                swing_mode="Auto",
                hvac_mode=HVAC_MODE_HEAT_COOL,
                hvac_action=None,
                aux=None,
                target_temp_high=24,
                target_temp_low=21,
                hvac_modes=[HVAC_MODE_HEAT_COOL, HVAC_MODE_COOL, HVAC_MODE_HEAT],
            ),
        ]
    )


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Demo climate devices config entry."""
    await async_setup_platform(hass, {}, async_add_entities)


class DemoClimate(ClimateEntity):
    """Representation of a demo climate device."""

    _attr_should_poll = False

    def __init__(
        self,
        unique_id,
        name,
        target_temperature,
        unit_of_measurement,
        preset,
        current_temperature,
        fan_mode,
        target_humidity,
        current_humidity,
        swing_mode,
        hvac_mode,
        hvac_action,
        aux,
        target_temp_high,
        target_temp_low,
        hvac_modes,
        preset_modes=None,
    ):
        """Initialize the climate device."""
        self._attr_unique_id = unique_id
        self._attr_name = name
        self._attr_supported_features = SUPPORT_FLAGS
        if target_temperature is not None:
            self._attr_supported_features = (
                self.supported_features | SUPPORT_TARGET_TEMPERATURE
            )
        if preset is not None:
            self._attr_supported_features = (
                self.supported_features | SUPPORT_PRESET_MODE
            )
        if fan_mode is not None:
            self._attr_supported_features = self.supported_features | SUPPORT_FAN_MODE
        if target_humidity is not None:
            self._attr_supported_features = (
                self.supported_features | SUPPORT_TARGET_HUMIDITY
            )
        if swing_mode is not None:
            self._attr_supported_features = self.supported_features | SUPPORT_SWING_MODE
        if aux is not None:
            self._attr_supported_features = self.supported_features | SUPPORT_AUX_HEAT
        if HVAC_MODE_HEAT_COOL in hvac_modes or HVAC_MODE_AUTO in hvac_modes:
            self._attr_supported_features = (
                self.supported_features | SUPPORT_TARGET_TEMPERATURE_RANGE
            )
        self._target_temperature = target_temperature
        self._target_humidity = target_humidity
        self._attr_temperature_unit = unit_of_measurement
        self._preset = preset
        self._attr_preset_modes = preset_modes
        self._current_temperature = current_temperature
        self._current_humidity = current_humidity
        self._current_fan_mode = fan_mode
        self._hvac_action = hvac_action
        self._hvac_mode = hvac_mode
        self._aux = aux
        self._current_swing_mode = swing_mode
        self._attr_fan_modes = ["On Low", "On High", "Auto Low", "Auto High", "Off"]
        self._attr_hvac_modes = hvac_modes
        self._attr_swing_modes = ["Auto", "1", "2", "3", "Off"]
        self._target_temperature_high = target_temp_high
        self._target_temperature_low = target_temp_low
        self._attr_device_info = {
            "identifiers": {
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, unique_id)
            },
            "name": name,
        }

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._current_temperature

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._target_temperature

    @property
    def target_temperature_high(self):
        """Return the highbound target temperature we try to reach."""
        return self._target_temperature_high

    @property
    def target_temperature_low(self):
        """Return the lowbound target temperature we try to reach."""
        return self._target_temperature_low

    @property
    def current_humidity(self):
        """Return the current humidity."""
        return self._current_humidity

    @property
    def target_humidity(self):
        """Return the humidity we try to reach."""
        return self._target_humidity

    @property
    def hvac_action(self):
        """Return current operation ie. heat, cool, idle."""
        return self._hvac_action

    @property
    def hvac_mode(self):
        """Return hvac target hvac state."""
        return self._hvac_mode

    @property
    def preset_mode(self):
        """Return preset mode."""
        return self._preset

    @property
    def is_aux_heat(self):
        """Return true if aux heat is on."""
        return self._aux

    @property
    def fan_mode(self):
        """Return the fan setting."""
        return self._current_fan_mode

    @property
    def swing_mode(self):
        """Return the swing setting."""
        return self._current_swing_mode

    async def async_set_temperature(self, **kwargs):
        """Set new target temperatures."""
        if kwargs.get(ATTR_TEMPERATURE) is not None:
            self._target_temperature = kwargs.get(ATTR_TEMPERATURE)
        if (
            kwargs.get(ATTR_TARGET_TEMP_HIGH) is not None
            and kwargs.get(ATTR_TARGET_TEMP_LOW) is not None
        ):
            self._target_temperature_high = kwargs.get(ATTR_TARGET_TEMP_HIGH)
            self._target_temperature_low = kwargs.get(ATTR_TARGET_TEMP_LOW)
        self.async_write_ha_state()

    async def async_set_humidity(self, humidity):
        """Set new humidity level."""
        self._target_humidity = humidity
        self.async_write_ha_state()

    async def async_set_swing_mode(self, swing_mode):
        """Set new swing mode."""
        self._current_swing_mode = swing_mode
        self.async_write_ha_state()

    async def async_set_fan_mode(self, fan_mode):
        """Set new fan mode."""
        self._current_fan_mode = fan_mode
        self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new operation mode."""
        self._hvac_mode = hvac_mode
        self.async_write_ha_state()

    async def async_set_preset_mode(self, preset_mode):
        """Update preset_mode on."""
        self._preset = preset_mode
        self.async_write_ha_state()

    async def async_turn_aux_heat_on(self):
        """Turn auxiliary heater on."""
        self._aux = True
        self.async_write_ha_state()

    async def async_turn_aux_heat_off(self):
        """Turn auxiliary heater off."""
        self._aux = False
        self.async_write_ha_state()

"""Support for ESPHome climate devices."""
from __future__ import annotations

from aioesphomeapi import (
    ClimateAction,
    ClimateFanMode,
    ClimateInfo,
    ClimateMode,
    ClimatePreset,
    ClimateState,
    ClimateSwingMode,
)

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    ATTR_HVAC_MODE,
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
    CURRENT_HVAC_COOL,
    CURRENT_HVAC_DRY,
    CURRENT_HVAC_FAN,
    CURRENT_HVAC_HEAT,
    CURRENT_HVAC_IDLE,
    CURRENT_HVAC_OFF,
    FAN_AUTO,
    FAN_DIFFUSE,
    FAN_FOCUS,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_MIDDLE,
    FAN_OFF,
    FAN_ON,
    HVAC_MODE_AUTO,
    HVAC_MODE_COOL,
    HVAC_MODE_DRY,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_HEAT,
    HVAC_MODE_HEAT_COOL,
    HVAC_MODE_OFF,
    PRESET_ACTIVITY,
    PRESET_AWAY,
    PRESET_BOOST,
    PRESET_COMFORT,
    PRESET_ECO,
    PRESET_HOME,
    PRESET_NONE,
    PRESET_SLEEP,
    SUPPORT_FAN_MODE,
    SUPPORT_PRESET_MODE,
    SUPPORT_SWING_MODE,
    SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_TARGET_TEMPERATURE_RANGE,
    SWING_BOTH,
    SWING_HORIZONTAL,
    SWING_OFF,
    SWING_VERTICAL,
)
from homeassistant.const import (
    ATTR_TEMPERATURE,
    PRECISION_HALVES,
    PRECISION_TENTHS,
    PRECISION_WHOLE,
    TEMP_CELSIUS,
)

from . import (
    EsphomeEntity,
    EsphomeEnumMapper,
    esphome_state_property,
    platform_async_setup_entry,
)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up ESPHome climate devices based on a config entry."""
    await platform_async_setup_entry(
        hass,
        entry,
        async_add_entities,
        component_key="climate",
        info_type=ClimateInfo,
        entity_type=EsphomeClimateEntity,
        state_type=ClimateState,
    )


_CLIMATE_MODES: EsphomeEnumMapper[ClimateMode] = EsphomeEnumMapper(
    {
        ClimateMode.OFF: HVAC_MODE_OFF,
        ClimateMode.HEAT_COOL: HVAC_MODE_HEAT_COOL,
        ClimateMode.COOL: HVAC_MODE_COOL,
        ClimateMode.HEAT: HVAC_MODE_HEAT,
        ClimateMode.FAN_ONLY: HVAC_MODE_FAN_ONLY,
        ClimateMode.DRY: HVAC_MODE_DRY,
        ClimateMode.AUTO: HVAC_MODE_AUTO,
    }
)
_CLIMATE_ACTIONS: EsphomeEnumMapper[ClimateAction] = EsphomeEnumMapper(
    {
        ClimateAction.OFF: CURRENT_HVAC_OFF,
        ClimateAction.COOLING: CURRENT_HVAC_COOL,
        ClimateAction.HEATING: CURRENT_HVAC_HEAT,
        ClimateAction.IDLE: CURRENT_HVAC_IDLE,
        ClimateAction.DRYING: CURRENT_HVAC_DRY,
        ClimateAction.FAN: CURRENT_HVAC_FAN,
    }
)
_FAN_MODES: EsphomeEnumMapper[ClimateFanMode] = EsphomeEnumMapper(
    {
        ClimateFanMode.ON: FAN_ON,
        ClimateFanMode.OFF: FAN_OFF,
        ClimateFanMode.AUTO: FAN_AUTO,
        ClimateFanMode.LOW: FAN_LOW,
        ClimateFanMode.MEDIUM: FAN_MEDIUM,
        ClimateFanMode.HIGH: FAN_HIGH,
        ClimateFanMode.MIDDLE: FAN_MIDDLE,
        ClimateFanMode.FOCUS: FAN_FOCUS,
        ClimateFanMode.DIFFUSE: FAN_DIFFUSE,
    }
)
_SWING_MODES: EsphomeEnumMapper[ClimateSwingMode] = EsphomeEnumMapper(
    {
        ClimateSwingMode.OFF: SWING_OFF,
        ClimateSwingMode.BOTH: SWING_BOTH,
        ClimateSwingMode.VERTICAL: SWING_VERTICAL,
        ClimateSwingMode.HORIZONTAL: SWING_HORIZONTAL,
    }
)
_PRESETS: EsphomeEnumMapper[ClimatePreset] = EsphomeEnumMapper(
    {
        ClimatePreset.NONE: PRESET_NONE,
        ClimatePreset.HOME: PRESET_HOME,
        ClimatePreset.AWAY: PRESET_AWAY,
        ClimatePreset.BOOST: PRESET_BOOST,
        ClimatePreset.COMFORT: PRESET_COMFORT,
        ClimatePreset.ECO: PRESET_ECO,
        ClimatePreset.SLEEP: PRESET_SLEEP,
        ClimatePreset.ACTIVITY: PRESET_ACTIVITY,
    }
)


class EsphomeClimateEntity(EsphomeEntity, ClimateEntity):
    """A climate implementation for ESPHome."""

    _attr_temperature_unit = TEMP_CELSIUS

    def __init__(self, entry_data, component_key: str, key: int) -> None:
        """Initialize a climate implementation for ESPHome."""
        super().__init__(entry_data, component_key, key)
        self._attr_precision = PRECISION_TENTHS
        for prec in [PRECISION_WHOLE, PRECISION_HALVES, PRECISION_TENTHS]:
            if self._static_info.visual_temperature_step >= prec:
                self._attr_precision = prec
        self._attr_hvac_modes = [
            _CLIMATE_MODES.from_esphome(mode)
            for mode in self._static_info.supported_modes
        ]
        self._attr_fan_modes = [
            _FAN_MODES.from_esphome(mode)
            for mode in self._static_info.supported_fan_modes
        ] + self._static_info.supported_custom_fan_modes
        self._attr_preset_modes = [
            _PRESETS.from_esphome(preset)
            for preset in self._static_info.supported_presets_compat(self._api_version)
        ] + self._static_info.supported_custom_presets
        self._attr_modes = [
            _SWING_MODES.from_esphome(mode)
            for mode in self._static_info.supported_swing_modes
        ]
        self._attr_target_temperature_step = round(
            self._static_info.visual_temperature_step, 1
        )
        self._attr_supported_features = 0
        if self._static_info.supports_two_point_target_temperature:
            self._attr_supported_features |= SUPPORT_TARGET_TEMPERATURE_RANGE
        else:
            self._attr_supported_features |= SUPPORT_TARGET_TEMPERATURE
        if self.preset_modes:
            self._attr_supported_features |= SUPPORT_PRESET_MODE
        if self._static_info.supported_fan_modes:
            self._attr_supported_features |= SUPPORT_FAN_MODE
        if self._static_info.supported_swing_modes:
            self._attr_supported_features |= SUPPORT_SWING_MODE

    @property
    def _static_info(self) -> ClimateInfo:
        return super()._static_info

    @property
    def _state(self) -> ClimateState | None:
        return super()._state

    @property
    def min_temp(self) -> float:
        """Return the minimum temperature."""
        return self._static_info.visual_min_temperature

    @property
    def max_temp(self) -> float:
        """Return the maximum temperature."""
        return self._static_info.visual_max_temperature

    # https://github.com/PyCQA/pylint/issues/3150 for all @esphome_state_property
    # pylint: disable=invalid-overridden-method

    @esphome_state_property
    def hvac_mode(self) -> str | None:
        """Return current operation ie. heat, cool, idle."""
        return _CLIMATE_MODES.from_esphome(self._state.mode)

    @esphome_state_property
    def hvac_action(self) -> str | None:
        """Return current action."""
        # HA has no support feature field for hvac_action
        if not self._static_info.supports_action:
            return None
        return _CLIMATE_ACTIONS.from_esphome(self._state.action)

    @esphome_state_property
    def fan_mode(self) -> str | None:
        """Return current fan setting."""
        return self._state.custom_fan_mode or _FAN_MODES.from_esphome(
            self._state.fan_mode
        )

    @esphome_state_property
    def preset_mode(self) -> str | None:
        """Return current preset mode."""
        return self._state.custom_preset or _PRESETS.from_esphome(
            self._state.preset_compat(self._api_version)
        )

    @esphome_state_property
    def swing_mode(self) -> str | None:
        """Return current swing mode."""
        return _SWING_MODES.from_esphome(self._state.swing_mode)

    @esphome_state_property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self._state.current_temperature

    @esphome_state_property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        return self._state.target_temperature

    @esphome_state_property
    def target_temperature_low(self) -> float | None:
        """Return the lowbound target temperature we try to reach."""
        return self._state.target_temperature_low

    @esphome_state_property
    def target_temperature_high(self) -> float | None:
        """Return the highbound target temperature we try to reach."""
        return self._state.target_temperature_high

    async def async_set_temperature(self, **kwargs) -> None:
        """Set new target temperature (and operation mode if set)."""
        data = {"key": self._static_info.key}
        if ATTR_HVAC_MODE in kwargs:
            data["mode"] = _CLIMATE_MODES.from_hass(kwargs[ATTR_HVAC_MODE])
        if ATTR_TEMPERATURE in kwargs:
            data["target_temperature"] = kwargs[ATTR_TEMPERATURE]
        if ATTR_TARGET_TEMP_LOW in kwargs:
            data["target_temperature_low"] = kwargs[ATTR_TARGET_TEMP_LOW]
        if ATTR_TARGET_TEMP_HIGH in kwargs:
            data["target_temperature_high"] = kwargs[ATTR_TARGET_TEMP_HIGH]
        await self._client.climate_command(**data)

    async def async_set_hvac_mode(self, hvac_mode: str) -> None:
        """Set new target operation mode."""
        await self._client.climate_command(
            key=self._static_info.key, mode=_CLIMATE_MODES.from_hass(hvac_mode)
        )

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set preset mode."""
        kwargs = {}
        if preset_mode in self._static_info.supported_custom_presets:
            kwargs["custom_preset"] = preset_mode
        else:
            kwargs["preset"] = _PRESETS.from_hass(preset_mode)
        await self._client.climate_command(key=self._static_info.key, **kwargs)

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """Set new fan mode."""
        kwargs = {}
        if fan_mode in self._static_info.supported_custom_fan_modes:
            kwargs["custom_fan_mode"] = fan_mode
        else:
            kwargs["fan_mode"] = _FAN_MODES.from_hass(fan_mode)
        await self._client.climate_command(key=self._static_info.key, **kwargs)

    async def async_set_swing_mode(self, swing_mode: str) -> None:
        """Set new swing mode."""
        await self._client.climate_command(
            key=self._static_info.key, swing_mode=_SWING_MODES.from_hass(swing_mode)
        )

"""Support for the Daikin HVAC."""
import logging

import voluptuous as vol

from homeassistant.components.climate import PLATFORM_SCHEMA, ClimateEntity
from homeassistant.components.climate.const import (
    ATTR_FAN_MODE,
    ATTR_HVAC_MODE,
    ATTR_PRESET_MODE,
    ATTR_SWING_MODE,
    CURRENT_HVAC_COOL,
    CURRENT_HVAC_HEAT,
    CURRENT_HVAC_IDLE,
    CURRENT_HVAC_OFF,
    HVAC_MODE_COOL,
    HVAC_MODE_DRY,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_HEAT,
    HVAC_MODE_HEAT_COOL,
    HVAC_MODE_OFF,
    PRESET_AWAY,
    PRESET_BOOST,
    PRESET_ECO,
    PRESET_NONE,
    SUPPORT_FAN_MODE,
    SUPPORT_PRESET_MODE,
    SUPPORT_SWING_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import ATTR_TEMPERATURE, CONF_HOST, CONF_NAME, TEMP_CELSIUS
import homeassistant.helpers.config_validation as cv

from . import DOMAIN as DAIKIN_DOMAIN
from .const import (
    ATTR_INSIDE_TEMPERATURE,
    ATTR_OUTSIDE_TEMPERATURE,
    ATTR_STATE_OFF,
    ATTR_STATE_ON,
    ATTR_TARGET_TEMPERATURE,
)

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {vol.Required(CONF_HOST): cv.string, vol.Optional(CONF_NAME): cv.string}
)

HA_STATE_TO_DAIKIN = {
    HVAC_MODE_FAN_ONLY: "fan",
    HVAC_MODE_DRY: "dry",
    HVAC_MODE_COOL: "cool",
    HVAC_MODE_HEAT: "hot",
    HVAC_MODE_HEAT_COOL: "auto",
    HVAC_MODE_OFF: "off",
}

DAIKIN_TO_HA_STATE = {
    "fan": HVAC_MODE_FAN_ONLY,
    "dry": HVAC_MODE_DRY,
    "cool": HVAC_MODE_COOL,
    "hot": HVAC_MODE_HEAT,
    "auto": HVAC_MODE_HEAT_COOL,
    "off": HVAC_MODE_OFF,
}

HA_STATE_TO_CURRENT_HVAC = {
    HVAC_MODE_COOL: CURRENT_HVAC_COOL,
    HVAC_MODE_HEAT: CURRENT_HVAC_HEAT,
    HVAC_MODE_OFF: CURRENT_HVAC_OFF,
}

HA_PRESET_TO_DAIKIN = {
    PRESET_AWAY: "on",
    PRESET_NONE: "off",
    PRESET_BOOST: "powerful",
    PRESET_ECO: "econo",
}

HA_ATTR_TO_DAIKIN = {
    ATTR_PRESET_MODE: "en_hol",
    ATTR_HVAC_MODE: "mode",
    ATTR_FAN_MODE: "f_rate",
    ATTR_SWING_MODE: "f_dir",
    ATTR_INSIDE_TEMPERATURE: "htemp",
    ATTR_OUTSIDE_TEMPERATURE: "otemp",
    ATTR_TARGET_TEMPERATURE: "stemp",
}

DAIKIN_ATTR_ADVANCED = "adv"


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Old way of setting up the Daikin HVAC platform.

    Can only be called when a user accidentally mentions the platform in their
    config. But even in that case it would have been ignored.
    """


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Daikin climate based on config_entry."""
    daikin_api = hass.data[DAIKIN_DOMAIN].get(entry.entry_id)
    async_add_entities([DaikinClimate(daikin_api)], update_before_add=True)


class DaikinClimate(ClimateEntity):
    """Representation of a Daikin HVAC."""

    _attr_target_temperature_step = 1
    _attr_temperature_unit = TEMP_CELSIUS

    def __init__(self, api):
        """Initialize the climate device."""

        self._api = api
        self._attr_name = api.name
        self._attr_unique_id = api.device.mac
        self._attr_device_info = api.device_info
        self._list = {
            ATTR_HVAC_MODE: list(HA_STATE_TO_DAIKIN),
            ATTR_FAN_MODE: api.device.fan_rate,
            ATTR_SWING_MODE: api.device.swing_modes,
        }
        self._attr_hvac_modes = self._list.get(ATTR_HVAC_MODE)
        self._attr_fan_modes = self._list.get(ATTR_FAN_MODE)
        self._attr_swing_modes = self._list.get(ATTR_SWING_MODE)
        self._attr_preset_modes = [PRESET_NONE]
        if api.device.support_away_mode:
            self._attr_preset_modes.append(PRESET_AWAY)
        if api.device.support_advanced_modes:
            self._attr_preset_modes += [PRESET_ECO, PRESET_BOOST]

        self._attr_supported_features = SUPPORT_TARGET_TEMPERATURE

        if api.device.support_away_mode or api.device.support_advanced_modes:
            self._attr_supported_features |= SUPPORT_PRESET_MODE

        if api.device.support_fan_rate:
            self._attr_supported_features |= SUPPORT_FAN_MODE

        if api.device.support_swing_mode:
            self._attr_supported_features |= SUPPORT_SWING_MODE

    async def _set(self, settings):
        """Set device settings using API."""
        values = {}

        for attr in [ATTR_TEMPERATURE, ATTR_FAN_MODE, ATTR_SWING_MODE, ATTR_HVAC_MODE]:
            value = settings.get(attr)
            if value is None:
                continue

            daikin_attr = HA_ATTR_TO_DAIKIN.get(attr)
            if daikin_attr is not None:
                if attr == ATTR_HVAC_MODE:
                    values[daikin_attr] = HA_STATE_TO_DAIKIN[value]
                elif value in self._list[attr]:
                    values[daikin_attr] = value.lower()
                else:
                    _LOGGER.error("Invalid value %s for %s", attr, value)

            # temperature
            elif attr == ATTR_TEMPERATURE:
                try:
                    values[HA_ATTR_TO_DAIKIN[ATTR_TARGET_TEMPERATURE]] = str(int(value))
                except ValueError:
                    _LOGGER.error("Invalid temperature %s", value)

        if values:
            await self._api.device.set(values)

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        await self._set(kwargs)

    async def async_set_hvac_mode(self, hvac_mode):
        """Set HVAC mode."""
        await self._set({ATTR_HVAC_MODE: hvac_mode})

    async def async_set_fan_mode(self, fan_mode):
        """Set fan mode."""
        await self._set({ATTR_FAN_MODE: fan_mode})

    async def async_set_swing_mode(self, swing_mode):
        """Set new target temperature."""
        await self._set({ATTR_SWING_MODE: swing_mode})

    async def async_set_preset_mode(self, preset_mode):
        """Set preset mode."""
        if preset_mode == PRESET_AWAY:
            await self._api.device.set_holiday(ATTR_STATE_ON)
        elif preset_mode == PRESET_BOOST:
            await self._api.device.set_advanced_mode(
                HA_PRESET_TO_DAIKIN[PRESET_BOOST], ATTR_STATE_ON
            )
        elif preset_mode == PRESET_ECO:
            await self._api.device.set_advanced_mode(
                HA_PRESET_TO_DAIKIN[PRESET_ECO], ATTR_STATE_ON
            )
        else:
            if self.preset_mode == PRESET_AWAY:
                await self._api.device.set_holiday(ATTR_STATE_OFF)
            elif self.preset_mode == PRESET_BOOST:
                await self._api.device.set_advanced_mode(
                    HA_PRESET_TO_DAIKIN[PRESET_BOOST], ATTR_STATE_OFF
                )
            elif self.preset_mode == PRESET_ECO:
                await self._api.device.set_advanced_mode(
                    HA_PRESET_TO_DAIKIN[PRESET_ECO], ATTR_STATE_OFF
                )

    async def async_update(self):
        """Retrieve latest state."""
        await self._api.async_update()
        daikin_mode = self._api.device.represent(HA_ATTR_TO_DAIKIN[ATTR_HVAC_MODE])[1]
        self._attr_hvac_mode = DAIKIN_TO_HA_STATE.get(daikin_mode, HVAC_MODE_HEAT_COOL)
        self._attr_fan_mode = self._api.device.represent(
            HA_ATTR_TO_DAIKIN[ATTR_FAN_MODE]
        )[1].title()
        self._attr_swing_mode = self._api.device.represent(
            HA_ATTR_TO_DAIKIN[ATTR_SWING_MODE]
        )[1].title()
        self._attr_current_temperature = self._api.device.inside_temperature
        self._attr_target_temperature = self._api.device.target_temperature
        ret = HA_STATE_TO_CURRENT_HVAC.get(self.hvac_mode)
        if (
            ret in (CURRENT_HVAC_COOL, CURRENT_HVAC_HEAT)
            and self._api.device.support_compressor_frequency
            and self._api.device.compressor_frequency == 0
        ):
            self._attr_hvac_action = CURRENT_HVAC_IDLE
        else:
            self._attr_hvac_action = ret

        if (
            self._api.device.represent(HA_ATTR_TO_DAIKIN[ATTR_PRESET_MODE])[1]
            == HA_PRESET_TO_DAIKIN[PRESET_AWAY]
        ):
            self._attr_preset_mode = PRESET_AWAY
        elif (
            HA_PRESET_TO_DAIKIN[PRESET_BOOST]
            in self._api.device.represent(DAIKIN_ATTR_ADVANCED)[1]
        ):
            self._attr_preset_mode = PRESET_BOOST
        elif (
            HA_PRESET_TO_DAIKIN[PRESET_ECO]
            in self._api.device.represent(DAIKIN_ATTR_ADVANCED)[1]
        ):
            self._attr_preset_mode = PRESET_ECO
        else:
            self._attr_preset_mode = PRESET_NONE

    async def async_turn_on(self):
        """Turn device on."""
        await self._api.device.set({})

    async def async_turn_off(self):
        """Turn device off."""
        await self._api.device.set(
            {HA_ATTR_TO_DAIKIN[ATTR_HVAC_MODE]: HA_STATE_TO_DAIKIN[HVAC_MODE_OFF]}
        )

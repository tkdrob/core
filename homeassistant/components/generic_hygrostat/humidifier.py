"""Adds support for generic hygrostat units."""
import asyncio
import logging

from homeassistant.components.humidifier import PLATFORM_SCHEMA, HumidifierEntity
from homeassistant.components.humidifier.const import (
    ATTR_HUMIDITY,
    DEVICE_CLASS_DEHUMIDIFIER,
    DEVICE_CLASS_HUMIDIFIER,
    MODE_AWAY,
    MODE_NORMAL,
    SUPPORT_MODES,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_MODE,
    CONF_NAME,
    EVENT_HOMEASSISTANT_START,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
)
from homeassistant.core import DOMAIN as HA_DOMAIN, callback
from homeassistant.helpers import condition
from homeassistant.helpers.event import (
    async_track_state_change,
    async_track_time_interval,
)
from homeassistant.helpers.restore_state import RestoreEntity

from . import (
    CONF_AWAY_FIXED,
    CONF_AWAY_HUMIDITY,
    CONF_DEVICE_CLASS,
    CONF_DRY_TOLERANCE,
    CONF_HUMIDIFIER,
    CONF_INITIAL_STATE,
    CONF_KEEP_ALIVE,
    CONF_MAX_HUMIDITY,
    CONF_MIN_DUR,
    CONF_MIN_HUMIDITY,
    CONF_SENSOR,
    CONF_STALE_DURATION,
    CONF_TARGET_HUMIDITY,
    CONF_WET_TOLERANCE,
    HYGROSTAT_SCHEMA,
)

_LOGGER = logging.getLogger(__name__)

ATTR_SAVED_HUMIDITY = "saved_humidity"

SUPPORT_FLAGS = 0

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(HYGROSTAT_SCHEMA.schema)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the generic hygrostat platform."""
    if discovery_info:
        config = discovery_info
    name = config[CONF_NAME]
    switch_entity_id = config[CONF_HUMIDIFIER]
    sensor_entity_id = config[CONF_SENSOR]
    min_humidity = config.get(CONF_MIN_HUMIDITY)
    max_humidity = config.get(CONF_MAX_HUMIDITY)
    target_humidity = config.get(CONF_TARGET_HUMIDITY)
    device_class = config.get(CONF_DEVICE_CLASS)
    min_cycle_duration = config.get(CONF_MIN_DUR)
    sensor_stale_duration = config.get(CONF_STALE_DURATION)
    dry_tolerance = config[CONF_DRY_TOLERANCE]
    wet_tolerance = config[CONF_WET_TOLERANCE]
    keep_alive = config.get(CONF_KEEP_ALIVE)
    initial_state = config.get(CONF_INITIAL_STATE)
    away_humidity = config.get(CONF_AWAY_HUMIDITY)
    away_fixed = config.get(CONF_AWAY_FIXED)

    async_add_entities(
        [
            GenericHygrostat(
                name,
                switch_entity_id,
                sensor_entity_id,
                min_humidity,
                max_humidity,
                target_humidity,
                device_class,
                min_cycle_duration,
                dry_tolerance,
                wet_tolerance,
                keep_alive,
                initial_state,
                away_humidity,
                away_fixed,
                sensor_stale_duration,
            )
        ]
    )


class GenericHygrostat(HumidifierEntity, RestoreEntity):
    """Representation of a Generic Hygrostat device."""

    _attr_should_poll = False

    def __init__(
        self,
        name,
        switch_entity_id,
        sensor_entity_id,
        min_humidity,
        max_humidity,
        target_humidity,
        device_class,
        min_cycle_duration,
        dry_tolerance,
        wet_tolerance,
        keep_alive,
        initial_state,
        away_humidity,
        away_fixed,
        sensor_stale_duration,
    ):
        """Initialize the hygrostat."""
        self._attr_name = name
        self._switch_entity_id = switch_entity_id
        self._sensor_entity_id = sensor_entity_id
        self._attr_device_class = device_class
        self._min_cycle_duration = min_cycle_duration
        self._dry_tolerance = dry_tolerance
        self._wet_tolerance = wet_tolerance
        self._keep_alive = keep_alive
        self._attr_is_on = initial_state
        self._saved_target_humidity = away_humidity or target_humidity
        self._attr_available = False
        self._cur_humidity = None
        self._humidity_lock = asyncio.Lock()
        self._attr_min_humidity = min_humidity
        self._attr_max_humidity = max_humidity
        self._attr_target_humidity = target_humidity
        self._attr_supported_features = SUPPORT_FLAGS
        if away_humidity:
            self._attr_supported_features = SUPPORT_FLAGS | SUPPORT_MODES
        self._away_humidity = away_humidity
        self._away_fixed = away_fixed
        self._sensor_stale_duration = sensor_stale_duration
        self._remove_stale_tracking = None
        self._attr_mode = MODE_NORMAL
        if not self.device_class:
            self._attr_device_class = DEVICE_CLASS_HUMIDIFIER
        if away_humidity:
            self._attr_available_modes = [MODE_NORMAL, MODE_AWAY]

    async def async_added_to_hass(self):
        """Run when entity about to be added."""
        await super().async_added_to_hass()

        # Add listener
        async_track_state_change(
            self.hass, self._sensor_entity_id, self._async_sensor_changed
        )
        async_track_state_change(
            self.hass, self._switch_entity_id, self._async_switch_changed
        )

        if self._keep_alive:
            async_track_time_interval(self.hass, self._async_operate, self._keep_alive)

        @callback
        async def _async_startup(event):
            """Init on startup."""
            sensor_state = self.hass.states.get(self._sensor_entity_id)
            await self._async_sensor_changed(self._sensor_entity_id, None, sensor_state)

        self.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, _async_startup)

        old_state = await self.async_get_last_state()
        if old_state is not None:
            if old_state.attributes.get(ATTR_MODE) == MODE_AWAY:
                self._attr_mode = MODE_AWAY
                self._saved_target_humidity = self.target_humidity
                self._attr_target_humidity = self._away_humidity or self.target_humidity
            if old_state.attributes.get(ATTR_HUMIDITY):
                self._attr_target_humidity = int(old_state.attributes[ATTR_HUMIDITY])
            if old_state.attributes.get(ATTR_SAVED_HUMIDITY):
                self._saved_target_humidity = int(
                    old_state.attributes[ATTR_SAVED_HUMIDITY]
                )
            if old_state.state:
                self._attr_is_on = old_state.state == STATE_ON
        if self.target_humidity is None:
            if self.device_class == DEVICE_CLASS_HUMIDIFIER:
                self._attr_target_humidity = super().min_humidity
            else:
                self._attr_target_humidity = super().max_humidity
            _LOGGER.warning(
                "No previously saved humidity, setting to %s", self.target_humidity
            )
        if self.is_on is None:
            self._attr_is_on = False

        await _async_startup(None)  # init the sensor

    @property
    def state_attributes(self):
        """Return the optional state attributes."""
        data = super().state_attributes

        if self._saved_target_humidity:
            data[ATTR_SAVED_HUMIDITY] = self._saved_target_humidity

        return data

    async def async_turn_on(self, **kwargs):
        """Turn hygrostat on."""
        if not self.available:
            return
        self._attr_is_on = True
        await self._async_operate(force=True)
        await self.async_update_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn hygrostat off."""
        if not self.available:
            return
        self._attr_is_on = False
        if self._is_device_active:
            await self._async_device_turn_off()
        await self.async_update_ha_state()

    async def async_set_humidity(self, humidity: int):
        """Set new target humidity."""
        if humidity is None:
            return

        if self.mode == MODE_AWAY and self._away_fixed:
            self._saved_target_humidity = humidity
            await self.async_update_ha_state()
            return

        self._attr_target_humidity = humidity
        await self._async_operate(force=True)
        await self.async_update_ha_state()

    @callback
    async def _async_sensor_changed(self, entity_id, old_state, new_state):
        """Handle ambient humidity changes."""
        if new_state is None:
            return

        if self._sensor_stale_duration:
            if self._remove_stale_tracking:
                self._remove_stale_tracking()
            self._remove_stale_tracking = async_track_time_interval(
                self.hass,
                self._async_sensor_not_responding,
                self._sensor_stale_duration,
            )

        await self._async_update_humidity(new_state.state)
        await self._async_operate()
        await self.async_update_ha_state()

    @callback
    async def _async_sensor_not_responding(self, now=None):
        """Handle sensor stale event."""

        _LOGGER.debug(
            "Sensor has not been updated for %s",
            now - self.hass.states.get(self._sensor_entity_id).last_updated,
        )
        _LOGGER.warning("Sensor is stalled, call the emergency stop")
        await self._async_update_humidity("Stalled")

    @callback
    def _async_switch_changed(self, entity_id, old_state, new_state):
        """Handle humidifier switch state changes."""
        if new_state is None:
            return
        self.async_schedule_update_ha_state()

    async def _async_update_humidity(self, humidity):
        """Update hygrostat with latest state from sensor."""
        try:
            self._cur_humidity = float(humidity)
        except ValueError as ex:
            _LOGGER.warning("Unable to update from sensor: %s", ex)
            self._cur_humidity = None
            self._attr_available = False
            if self._is_device_active:
                await self._async_device_turn_off()

    async def _async_operate(self, time=None, force=False):
        """Check if we need to turn humidifying on or off."""
        async with self._humidity_lock:
            if not self.available and None not in (
                self._cur_humidity,
                self.target_humidity,
            ):
                self._attr_available = True
                force = True
                _LOGGER.info(
                    "Obtained current and target humidity. "
                    "Generic hygrostat active. %s, %s",
                    self._cur_humidity,
                    self.target_humidity,
                )

            if not self.available or not self.is_on:
                return

            if not force and time is None:
                # If the `force` argument is True, we
                # ignore `min_cycle_duration`.
                # If the `time` argument is not none, we were invoked for
                # keep-alive purposes, and `min_cycle_duration` is irrelevant.
                if self._min_cycle_duration:
                    if self._is_device_active:
                        current_state = STATE_ON
                    else:
                        current_state = STATE_OFF
                    long_enough = condition.state(
                        self.hass,
                        self._switch_entity_id,
                        current_state,
                        self._min_cycle_duration,
                    )
                    if not long_enough:
                        return

            if force:
                # Ignore the tolerance when switched on manually
                dry_tolerance = 0
                wet_tolerance = 0
            else:
                dry_tolerance = self._dry_tolerance
                wet_tolerance = self._wet_tolerance

            too_dry = self.target_humidity - self._cur_humidity >= dry_tolerance
            too_wet = self._cur_humidity - self.target_humidity >= wet_tolerance
            if self._is_device_active:
                if (self.device_class == DEVICE_CLASS_HUMIDIFIER and too_wet) or (
                    self.device_class == DEVICE_CLASS_DEHUMIDIFIER and too_dry
                ):
                    _LOGGER.info("Turning off humidifier %s", self._switch_entity_id)
                    await self._async_device_turn_off()
                elif time is not None:
                    # The time argument is passed only in keep-alive case
                    await self._async_device_turn_on()
            else:
                if (self.device_class == DEVICE_CLASS_HUMIDIFIER and too_dry) or (
                    self.device_class == DEVICE_CLASS_DEHUMIDIFIER and too_wet
                ):
                    _LOGGER.info("Turning on humidifier %s", self._switch_entity_id)
                    await self._async_device_turn_on()
                elif time is not None:
                    # The time argument is passed only in keep-alive case
                    await self._async_device_turn_off()

    @property
    def _is_device_active(self):
        """If the toggleable device is currently active."""
        return self.hass.states.is_state(self._switch_entity_id, STATE_ON)

    async def _async_device_turn_on(self):
        """Turn humidifier toggleable device on."""
        data = {ATTR_ENTITY_ID: self._switch_entity_id}
        await self.hass.services.async_call(HA_DOMAIN, SERVICE_TURN_ON, data)

    async def _async_device_turn_off(self):
        """Turn humidifier toggleable device off."""
        data = {ATTR_ENTITY_ID: self._switch_entity_id}
        await self.hass.services.async_call(HA_DOMAIN, SERVICE_TURN_OFF, data)

    async def async_set_mode(self, mode: str):
        """Set new mode.

        This method must be run in the event loop and returns a coroutine.
        """
        if self._away_humidity is None:
            return
        if mode == MODE_AWAY and self.mode != MODE_AWAY:
            self._attr_mode = MODE_AWAY
            if not self._saved_target_humidity:
                self._saved_target_humidity = self._away_humidity
            self._saved_target_humidity, self._attr_target_humidity = (
                self.target_humidity,
                self._saved_target_humidity,
            )
            await self._async_operate(force=True)
        elif mode == MODE_NORMAL and self.mode != MODE_NORMAL:
            self._attr_mode = MODE_NORMAL
            self._saved_target_humidity, self._attr_target_humidity = (
                self.target_humidity,
                self._saved_target_humidity,
            )
            await self._async_operate(force=True)

        await self.async_update_ha_state()

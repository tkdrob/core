"""Support for Dexcom sensors."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import CONF_UNIT_OF_MEASUREMENT, CONF_USERNAME
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import COORDINATOR, DOMAIN, GLUCOSE_TREND_ICON, GLUCOSE_VALUE_ICON, MG_DL


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Dexcom sensors."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id][COORDINATOR]
    username = config_entry.data[CONF_USERNAME]
    unit_of_measurement = config_entry.options[CONF_UNIT_OF_MEASUREMENT]
    sensors = []
    sensors.append(DexcomGlucoseTrendSensor(coordinator, username))
    sensors.append(DexcomGlucoseValueSensor(coordinator, username, unit_of_measurement))
    async_add_entities(sensors, False)


class DexcomGlucoseValueSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Dexcom glucose value sensor."""

    _attr_icon = GLUCOSE_VALUE_ICON

    def __init__(self, coordinator, username, unit_of_measurement):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._state = None
        self._attr_unit_of_measurement = unit_of_measurement
        self._attribute_unit_of_measurement = (
            "mg_dl" if unit_of_measurement == MG_DL else "mmol_l"
        )
        self._attr_name = f"{DOMAIN}_{username}_glucose_value"
        self._attr_unique_id = f"{username}-value"

    @property
    def state(self):
        """Return the state of the sensor."""
        if self.coordinator.data:
            return getattr(self.coordinator.data, self._attribute_unit_of_measurement)
        return None


class DexcomGlucoseTrendSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Dexcom glucose trend sensor."""

    def __init__(self, coordinator, username):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._state = None
        self._attr_name = f"{DOMAIN}_{username}_glucose_trend"
        self._attr_unique_id = f"{username}-trend"
        if coordinator.data:
            self._attr_icon = GLUCOSE_TREND_ICON[coordinator.data.trend]
        else:
            self._attr_icon = GLUCOSE_TREND_ICON[0]

    @property
    def state(self):
        """Return the state of the sensor."""
        if self.coordinator.data:
            return self.coordinator.data.trend_description
        return None

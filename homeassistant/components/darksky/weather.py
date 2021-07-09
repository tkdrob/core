"""Support for retrieving meteorological data from Dark Sky."""
from datetime import timedelta
import logging

import forecastio
from requests.exceptions import ConnectionError as ConnectError, HTTPError, Timeout
import voluptuous as vol

from homeassistant.components.weather import (
    ATTR_CONDITION_CLEAR_NIGHT,
    ATTR_CONDITION_CLOUDY,
    ATTR_CONDITION_FOG,
    ATTR_CONDITION_HAIL,
    ATTR_CONDITION_LIGHTNING,
    ATTR_CONDITION_PARTLYCLOUDY,
    ATTR_CONDITION_RAINY,
    ATTR_CONDITION_SNOWY,
    ATTR_CONDITION_SNOWY_RAINY,
    ATTR_CONDITION_SUNNY,
    ATTR_CONDITION_WINDY,
    ATTR_FORECAST_CONDITION,
    ATTR_FORECAST_PRECIPITATION,
    ATTR_FORECAST_TEMP,
    ATTR_FORECAST_TEMP_LOW,
    ATTR_FORECAST_TIME,
    ATTR_FORECAST_WIND_BEARING,
    ATTR_FORECAST_WIND_SPEED,
    PLATFORM_SCHEMA,
    WeatherEntity,
)
from homeassistant.const import (
    CONF_API_KEY,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_MODE,
    CONF_NAME,
    PRESSURE_HPA,
    PRESSURE_INHG,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
)
import homeassistant.helpers.config_validation as cv
from homeassistant.util import Throttle
from homeassistant.util.dt import utc_from_timestamp
from homeassistant.util.pressure import convert as convert_pressure

_LOGGER = logging.getLogger(__name__)

ATTRIBUTION = "Powered by Dark Sky"

FORECAST_MODE = ["hourly", "daily"]

MAP_CONDITION = {
    "clear-day": ATTR_CONDITION_SUNNY,
    "clear-night": ATTR_CONDITION_CLEAR_NIGHT,
    "rain": ATTR_CONDITION_RAINY,
    "snow": ATTR_CONDITION_SNOWY,
    "sleet": ATTR_CONDITION_SNOWY_RAINY,
    "wind": ATTR_CONDITION_WINDY,
    "fog": ATTR_CONDITION_FOG,
    "cloudy": ATTR_CONDITION_CLOUDY,
    "partly-cloudy-day": ATTR_CONDITION_PARTLYCLOUDY,
    "partly-cloudy-night": ATTR_CONDITION_PARTLYCLOUDY,
    "hail": ATTR_CONDITION_HAIL,
    "thunderstorm": ATTR_CONDITION_LIGHTNING,
    "tornado": None,
}

CONF_UNITS = "units"

DEFAULT_NAME = "Dark Sky"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_API_KEY): cv.string,
        vol.Optional(CONF_LATITUDE): cv.latitude,
        vol.Optional(CONF_LONGITUDE): cv.longitude,
        vol.Optional(CONF_MODE, default="hourly"): vol.In(FORECAST_MODE),
        vol.Optional(CONF_UNITS): vol.In(["auto", "si", "us", "ca", "uk", "uk2"]),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    }
)

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=3)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Dark Sky weather."""
    latitude = config.get(CONF_LATITUDE, hass.config.latitude)
    longitude = config.get(CONF_LONGITUDE, hass.config.longitude)
    name = config.get(CONF_NAME)
    mode = config.get(CONF_MODE)

    units = config.get(CONF_UNITS)
    if not units:
        units = "ca" if hass.config.units.is_metric else "us"

    dark_sky = DarkSkyData(config.get(CONF_API_KEY), latitude, longitude, units)

    add_entities([DarkSkyWeather(name, dark_sky, mode)], True)


class DarkSkyWeather(WeatherEntity):
    """Representation of a weather condition."""

    def __init__(self, name, dark_sky, mode):
        """Initialize Dark Sky weather."""
        self._attr_name = name
        self._dark_sky = dark_sky
        self._mode = mode

        self._ds_hourly = None
        self._ds_daily = None
        if self._dark_sky.units is None:
            self._attr_temperature_unit = None
        elif "us" in self._dark_sky.units:
            self._attr_temperature_unit = TEMP_FAHRENHEIT
        else:
            self._attr_temperature_unit = TEMP_CELSIUS

    @property
    def forecast(self):
        """Return the forecast array."""
        # Per conversation with Joshua Reyes of Dark Sky, to get the total
        # forecasted precipitation, you have to multiple the intensity by
        # the hours for the forecast interval
        def calc_precipitation(intensity, hours):
            amount = None
            if intensity is not None:
                amount = round((intensity * hours), 1)
            return amount if amount > 0 else None

        data = None

        if self._mode == "daily":
            data = [
                {
                    ATTR_FORECAST_TIME: utc_from_timestamp(
                        entry.d.get("time")
                    ).isoformat(),
                    ATTR_FORECAST_TEMP: entry.d.get("temperatureHigh"),
                    ATTR_FORECAST_TEMP_LOW: entry.d.get("temperatureLow"),
                    ATTR_FORECAST_PRECIPITATION: calc_precipitation(
                        entry.d.get("precipIntensity"), 24
                    ),
                    ATTR_FORECAST_WIND_SPEED: entry.d.get("windSpeed"),
                    ATTR_FORECAST_WIND_BEARING: entry.d.get("windBearing"),
                    ATTR_FORECAST_CONDITION: MAP_CONDITION.get(entry.d.get("icon")),
                }
                for entry in self._ds_daily.data
            ]
        else:
            data = [
                {
                    ATTR_FORECAST_TIME: utc_from_timestamp(
                        entry.d.get("time")
                    ).isoformat(),
                    ATTR_FORECAST_TEMP: entry.d.get("temperature"),
                    ATTR_FORECAST_PRECIPITATION: calc_precipitation(
                        entry.d.get("precipIntensity"), 1
                    ),
                    ATTR_FORECAST_CONDITION: MAP_CONDITION.get(entry.d.get("icon")),
                }
                for entry in self._ds_hourly.data
            ]

        return data

    def update(self):
        """Get the latest data from Dark Sky."""
        self._dark_sky.update()

        self._attr_available = self._dark_sky.data is not None
        ds_currently = self._dark_sky.currently.d if self._dark_sky.currently else {}
        self._ds_hourly = self._dark_sky.hourly
        self._ds_daily = self._dark_sky.daily
        self._attr_attribution = ATTRIBUTION
        self._attr_temperature = ds_currently.get("temperature")
        self._attr_humidity = round(ds_currently.get("humidity") * 100.0, 2)
        self._attr_wind_speed = ds_currently.get("windSpeed")
        self._attr_wind_bearing = ds_currently.get("windBearing")
        self._attr_ozone = ds_currently.get("ozone")
        if "us" in self._dark_sky.units:
            self._attr_pressure = round(
                convert_pressure(
                    ds_currently.get("pressure"), PRESSURE_HPA, PRESSURE_INHG
                ),
                2,
            )
        else:
            self._attr_pressure = ds_currently.get("pressure")
        self._attr_visibility = ds_currently.get("visibility")
        self._attr_condition = MAP_CONDITION.get(ds_currently.get("icon"))


class DarkSkyData:
    """Get the latest data from Dark Sky."""

    def __init__(self, api_key, latitude, longitude, units):
        """Initialize the data object."""
        self._api_key = api_key
        self.latitude = latitude
        self.longitude = longitude
        self.requested_units = units

        self.data = None
        self.currently = None
        self.hourly = None
        self.daily = None
        self._connect_error = False

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Get the latest data from Dark Sky."""
        try:
            self.data = forecastio.load_forecast(
                self._api_key, self.latitude, self.longitude, units=self.requested_units
            )
            self.currently = self.data.currently()
            self.hourly = self.data.hourly()
            self.daily = self.data.daily()
            if self._connect_error:
                self._connect_error = False
                _LOGGER.info("Reconnected to Dark Sky")
        except (ConnectError, HTTPError, Timeout, ValueError) as error:
            if not self._connect_error:
                self._connect_error = True
                _LOGGER.error("Unable to connect to Dark Sky. %s", error)
            self.data = None

    @property
    def units(self):
        """Get the unit system of returned data."""
        if self.data is None:
            return None
        return self.data.json.get("flags").get("units")

"""Platform for retrieving meteorological data from Environment Canada."""
import datetime
import re

from env_canada import ECData
import voluptuous as vol

from homeassistant.components.weather import (
    ATTR_CONDITION_CLEAR_NIGHT,
    ATTR_CONDITION_CLOUDY,
    ATTR_CONDITION_FOG,
    ATTR_CONDITION_HAIL,
    ATTR_CONDITION_LIGHTNING_RAINY,
    ATTR_CONDITION_PARTLYCLOUDY,
    ATTR_CONDITION_POURING,
    ATTR_CONDITION_RAINY,
    ATTR_CONDITION_SNOWY,
    ATTR_CONDITION_SNOWY_RAINY,
    ATTR_CONDITION_SUNNY,
    ATTR_CONDITION_WINDY,
    ATTR_FORECAST_CONDITION,
    ATTR_FORECAST_PRECIPITATION_PROBABILITY,
    ATTR_FORECAST_TEMP,
    ATTR_FORECAST_TEMP_LOW,
    ATTR_FORECAST_TIME,
    PLATFORM_SCHEMA,
    WeatherEntity,
)
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME, TEMP_CELSIUS
import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt

CONF_FORECAST = "forecast"
CONF_ATTRIBUTION = "Data provided by Environment Canada"
CONF_STATION = "station"


def validate_station(station):
    """Check that the station ID is well-formed."""
    if station is None:
        return
    if not re.fullmatch(r"[A-Z]{2}/s0000\d{3}", station):
        raise vol.error.Invalid('Station ID must be of the form "XX/s0000###"')
    return station


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME): cv.string,
        vol.Optional(CONF_STATION): validate_station,
        vol.Inclusive(CONF_LATITUDE, "latlon"): cv.latitude,
        vol.Inclusive(CONF_LONGITUDE, "latlon"): cv.longitude,
        vol.Optional(CONF_FORECAST, default="daily"): vol.In(["daily", "hourly"]),
    }
)

# Icon codes from http://dd.weatheroffice.ec.gc.ca/citypage_weather/
# docs/current_conditions_icon_code_descriptions_e.csv
ICON_CONDITION_MAP = {
    ATTR_CONDITION_SUNNY: [0, 1],
    ATTR_CONDITION_CLEAR_NIGHT: [30, 31],
    ATTR_CONDITION_PARTLYCLOUDY: [2, 3, 4, 5, 22, 32, 33, 34, 35],
    ATTR_CONDITION_CLOUDY: [10],
    ATTR_CONDITION_RAINY: [6, 9, 11, 12, 28, 36],
    ATTR_CONDITION_LIGHTNING_RAINY: [19, 39, 46, 47],
    ATTR_CONDITION_POURING: [13],
    ATTR_CONDITION_SNOWY_RAINY: [7, 14, 15, 27, 37],
    ATTR_CONDITION_SNOWY: [8, 16, 17, 18, 25, 26, 38, 40],
    ATTR_CONDITION_WINDY: [43],
    ATTR_CONDITION_FOG: [20, 21, 23, 24, 44],
    ATTR_CONDITION_HAIL: [26, 27],
}


def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the Environment Canada weather."""
    if config.get(CONF_STATION):
        ec_data = ECData(station_id=config[CONF_STATION])
    else:
        lat = config.get(CONF_LATITUDE, hass.config.latitude)
        lon = config.get(CONF_LONGITUDE, hass.config.longitude)
        ec_data = ECData(coordinates=(lat, lon))

    add_devices([ECWeather(ec_data, config)])


class ECWeather(WeatherEntity):
    """Representation of a weather condition."""

    _attr_attribution = CONF_ATTRIBUTION
    _attr_temperature_unit = TEMP_CELSIUS

    def __init__(self, ec_data, config):
        """Initialize Environment Canada weather."""
        self.ec_data = ec_data
        self.forecast_type = config[CONF_FORECAST]
        self._attr_name = ec_data.metadata.get("location")
        if config.get(CONF_NAME):
            self._attr_name = config.get(CONF_NAME)

    def update(self):
        """Get the latest data from Environment Canada."""
        data = self.ec_data.update()
        self._attr_temperature = self._attr_humidity = self._attr_wind_speed = None
        self._attr_wind_bearing = self._attr_wind_bearing = None
        self._attr_visibility = icon_code = None
        if data.conditions.get("temperature", {}).get("value"):
            self._attr_temperature = float(data.conditions["temperature"]["value"])
        elif data.hourly_forecasts[0].get("temperature"):
            self._attr_temperature = float(data.hourly_forecasts[0]["temperature"])
        if data.conditions.get("humidity", {}).get("value"):
            self._attr_humidity = float(data.conditions["humidity"]["value"])
        if data.conditions.get("wind_speed", {}).get("value"):
            self._attr_wind_speed = float(data.conditions["wind_speed"]["value"])
        if data.conditions.get("wind_bearing", {}).get("value"):
            self._attr_wind_bearing = float(data.conditions["wind_bearing"]["value"])
        if data.conditions.get("pressure", {}).get("value"):
            self._attr_pressure = 10 * float(data.conditions["pressure"]["value"])
        if data.conditions.get("visibility", {}).get("value"):
            self._attr_visibility = float(data.conditions["visibility"]["value"])
        if data.conditions.get("icon_code", {}).get("value"):
            icon_code = data.conditions["icon_code"]["value"]
        elif data.hourly_forecasts[0].get("icon_code"):
            icon_code = data.hourly_forecasts[0]["icon_code"]
        self._attr_condition = ""
        if icon_code:
            self._attr_condition = icon_code_to_condition(int(icon_code))
        self._attr_forecast = get_forecast(data, self.forecast_type)


def get_forecast(ec_data, forecast_type):
    """Build the forecast array."""
    forecast_array = []

    if forecast_type == "daily":
        half_days = ec_data.daily_forecasts

        today = {
            ATTR_FORECAST_TIME: dt.now().isoformat(),
            ATTR_FORECAST_CONDITION: icon_code_to_condition(
                int(half_days[0]["icon_code"])
            ),
            ATTR_FORECAST_PRECIPITATION_PROBABILITY: int(
                half_days[0]["precip_probability"]
            ),
        }

        if half_days[0]["temperature_class"] == "high":
            today.update(
                {
                    ATTR_FORECAST_TEMP: int(half_days[0]["temperature"]),
                    ATTR_FORECAST_TEMP_LOW: int(half_days[1]["temperature"]),
                }
            )
            half_days = half_days[2:]
        else:
            today.update(
                {
                    ATTR_FORECAST_TEMP: None,
                    ATTR_FORECAST_TEMP_LOW: int(half_days[0]["temperature"]),
                }
            )
            half_days = half_days[1:]

        forecast_array.append(today)

        for day, high, low in zip(range(1, 6), range(0, 9, 2), range(1, 10, 2)):
            forecast_array.append(
                {
                    ATTR_FORECAST_TIME: (
                        dt.now() + datetime.timedelta(days=day)
                    ).isoformat(),
                    ATTR_FORECAST_TEMP: int(half_days[high]["temperature"]),
                    ATTR_FORECAST_TEMP_LOW: int(half_days[low]["temperature"]),
                    ATTR_FORECAST_CONDITION: icon_code_to_condition(
                        int(half_days[high]["icon_code"])
                    ),
                    ATTR_FORECAST_PRECIPITATION_PROBABILITY: int(
                        half_days[high]["precip_probability"]
                    ),
                }
            )

    elif forecast_type == "hourly":
        for hour in ec_data.hourly_forecasts:
            forecast_array.append(
                {
                    ATTR_FORECAST_TIME: datetime.datetime.strptime(
                        hour["period"], "%Y%m%d%H%M%S"
                    )
                    .replace(tzinfo=dt.UTC)
                    .isoformat(),
                    ATTR_FORECAST_TEMP: int(hour["temperature"]),
                    ATTR_FORECAST_CONDITION: icon_code_to_condition(
                        int(hour["icon_code"])
                    ),
                    ATTR_FORECAST_PRECIPITATION_PROBABILITY: int(
                        hour["precip_probability"]
                    ),
                }
            )

    return forecast_array


def icon_code_to_condition(icon_code):
    """Return the condition corresponding to an icon code."""
    for condition, codes in ICON_CONDITION_MAP.items():
        if icon_code in codes:
            return condition
    return None

"""Support for Decora dimmers."""
import copy
from functools import wraps
import logging
import time

from bluepy.btle import BTLEException  # pylint: disable=import-error
import decora  # pylint: disable=import-error
import voluptuous as vol

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    PLATFORM_SCHEMA,
    SUPPORT_BRIGHTNESS,
    LightEntity,
)
from homeassistant.const import CONF_API_KEY, CONF_DEVICES, CONF_NAME
import homeassistant.helpers.config_validation as cv
import homeassistant.util as util

_LOGGER = logging.getLogger(__name__)

SUPPORT_DECORA_LED = SUPPORT_BRIGHTNESS


def _name_validator(config):
    """Validate the name."""
    config = copy.deepcopy(config)
    for address, device_config in config[CONF_DEVICES].items():
        if CONF_NAME not in device_config:
            device_config[CONF_NAME] = util.slugify(address)

    return config


DEVICE_SCHEMA = vol.Schema(
    {vol.Optional(CONF_NAME): cv.string, vol.Required(CONF_API_KEY): cv.string}
)

PLATFORM_SCHEMA = vol.Schema(
    vol.All(
        PLATFORM_SCHEMA.extend(
            {vol.Optional(CONF_DEVICES, default={}): {cv.string: DEVICE_SCHEMA}}
        ),
        _name_validator,
    )
)


def retry(method):
    """Retry bluetooth commands."""

    @wraps(method)
    def wrapper_retry(device, *args, **kwargs):
        """Try send command and retry on error."""

        initial = time.monotonic()
        while True:
            if time.monotonic() - initial >= 10:
                return None
            try:
                return method(device, *args, **kwargs)
            except (decora.decoraException, AttributeError, BTLEException):
                _LOGGER.warning(
                    "Decora connect error for device %s. Reconnecting",
                    device.name,
                )
                # pylint: disable=protected-access
                device._switch.connect()

    return wrapper_retry


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up an Decora switch."""
    lights = []
    for address, device_config in config[CONF_DEVICES].items():
        device = {}
        device["name"] = device_config[CONF_NAME]
        device["key"] = device_config[CONF_API_KEY]
        device["address"] = address
        light = DecoraLight(device)
        lights.append(light)

    add_entities(lights)


class DecoraLight(LightEntity):
    """Representation of an Decora light."""

    _attr_assumed_state = False
    _attr_supported_features = SUPPORT_DECORA_LED

    def __init__(self, device):
        """Initialize the light."""

        self._attr_name = device["name"]
        self._attr_unique_id = device["address"]
        self._switch = decora.decora(self.unique_id, device["key"])
        self._attr_brightness = 0

    @retry
    def set_state(self, brightness):
        """Set the state of this lamp to the provided brightness."""
        self._switch.set_brightness(int(brightness / 2.55))
        self._attr_brightness = brightness

    @retry
    def turn_on(self, **kwargs):
        """Turn the specified or all lights on."""
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        self._switch.on()
        self._attr_state = True

        if brightness is not None:
            self.set_state(brightness)

    @retry
    def turn_off(self, **kwargs):
        """Turn the specified or all lights off."""
        self._switch.off()
        self._attr_state = False

    @retry
    def update(self):
        """Synchronise internal state with the actual light state."""
        self._attr_brightness = self._switch.get_brightness() * 2.55
        self._attr_state = self._switch.get_on()

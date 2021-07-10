"""Support for interacting with Digital Ocean droplets."""
import logging

import voluptuous as vol

from homeassistant.components.switch import PLATFORM_SCHEMA, SwitchEntity
from homeassistant.const import ATTR_ATTRIBUTION
import homeassistant.helpers.config_validation as cv

from . import (
    ATTR_CREATED_AT,
    ATTR_DROPLET_ID,
    ATTR_DROPLET_NAME,
    ATTR_FEATURES,
    ATTR_IPV4_ADDRESS,
    ATTR_IPV6_ADDRESS,
    ATTR_MEMORY,
    ATTR_REGION,
    ATTR_VCPUS,
    ATTRIBUTION,
    CONF_DROPLETS,
    DATA_DIGITAL_OCEAN,
)

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "Droplet"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {vol.Required(CONF_DROPLETS): vol.All(cv.ensure_list, [cv.string])}
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the Digital Ocean droplet switch."""
    digital = hass.data.get(DATA_DIGITAL_OCEAN)
    if not digital:
        return False

    droplets = config[CONF_DROPLETS]

    dev = []
    for droplet in droplets:
        droplet_id = digital.get_droplet_id(droplet)
        if droplet_id is None:
            _LOGGER.error("Droplet %s is not available", droplet)
            return False
        dev.append(DigitalOceanSwitch(digital, droplet_id))

    add_entities(dev, True)


class DigitalOceanSwitch(SwitchEntity):
    """Representation of a Digital Ocean droplet switch."""

    def __init__(self, do, droplet_id):
        """Initialize a new Digital Ocean sensor."""
        self._digital_ocean = do
        self._droplet_id = droplet_id
        self.data = None

    def turn_on(self, **kwargs):
        """Boot-up the droplet."""
        if self.data.status != "active":
            self.data.power_on()

    def turn_off(self, **kwargs):
        """Shutdown the droplet."""
        if self.data.status == "active":
            self.data.power_off()

    def update(self):
        """Get the latest data from the device and update the data."""
        self._digital_ocean.update()

        for droplet in self._digital_ocean.data:
            if droplet.id == self._droplet_id:
                self.data = droplet
                self._attr_name = droplet.name
                self._attr_is_on = droplet.status == "active"
                self._attr_extra_state_attributes = {
                    ATTR_ATTRIBUTION: ATTRIBUTION,
                    ATTR_CREATED_AT: droplet.created_at,
                    ATTR_DROPLET_ID: droplet.id,
                    ATTR_DROPLET_NAME: droplet.name,
                    ATTR_FEATURES: droplet.features,
                    ATTR_IPV4_ADDRESS: droplet.ip_address,
                    ATTR_IPV6_ADDRESS: droplet.ip_v6_address,
                    ATTR_MEMORY: droplet.memory,
                    ATTR_REGION: droplet.region["name"],
                    ATTR_VCPUS: droplet.vcpus,
                }

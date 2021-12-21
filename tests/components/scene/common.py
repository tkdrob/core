"""Collection of helper methods.

All containing methods are legacy helpers that should not be used by new
components. Instead call the service directly.
"""
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ENTITY_MATCH_ALL,
    SERVICE_TURN_ON,
    Platform,
)
from homeassistant.loader import bind_hass


@bind_hass
def activate(hass, entity_id=ENTITY_MATCH_ALL):
    """Activate a scene."""
    data = {}

    if entity_id:
        data[ATTR_ENTITY_ID] = entity_id

    hass.services.call(Platform.SCENE, SERVICE_TURN_ON, data)

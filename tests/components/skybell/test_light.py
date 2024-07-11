"""Light tests for the Skybell integration."""

from contextlib import suppress
from unittest.mock import patch

from syrupy.assertion import SnapshotAssertion

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_RGB_COLOR,
    DOMAIN as LIGHT_DOMAIN,
)
from homeassistant.const import ATTR_ENTITY_ID, SERVICE_TURN_OFF, SERVICE_TURN_ON
from homeassistant.core import HomeAssistant


async def test_light(
    hass: HomeAssistant, setup_integration: None, snapshot: SnapshotAssertion
) -> None:
    """Test light entity."""
    entity_id = "light.front_door_led_color"
    state = hass.states.get(entity_id)
    assert state == snapshot(name=entity_id)

    patched = "homeassistant.components.skybell.api.device.SkybellDevice._set_setting"
    with suppress(AttributeError), patch(patched) as mock:
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {
                ATTR_ENTITY_ID: entity_id,
                ATTR_RGB_COLOR: (13, 25, 255),
                ATTR_BRIGHTNESS: 107,
            },
            blocking=True,
        )
    assert list(mock.call_args) == snapshot(name=f"{entity_id}_on")

    with suppress(AttributeError), patch(patched) as mock:
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
    assert list(mock.call_args) == snapshot(name=f"{entity_id}_off")

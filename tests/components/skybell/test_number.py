"""Number tests for the Skybell integration."""

from contextlib import suppress
from unittest.mock import patch

import pytest
from syrupy.assertion import SnapshotAssertion

from homeassistant.components.number import (
    ATTR_VALUE,
    DOMAIN as NUMBER_DOMAIN,
    SERVICE_SET_VALUE,
)
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant


@pytest.mark.parametrize(
    "entity_id",
    [
        "number.front_door_motion_sensitivity",
        "number.front_door_pir_sensitivity",
    ],
)
@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_numbers(
    hass: HomeAssistant,
    setup_integration: None,
    snapshot: SnapshotAssertion,
    entity_id: str,
) -> None:
    """Test number entities."""
    assert hass.states.get(entity_id) == snapshot

    patched = "homeassistant.components.skybell.api.device.SkybellDevice._set_setting"
    with suppress(AttributeError), patch(patched) as mock:
        await hass.services.async_call(
            NUMBER_DOMAIN,
            SERVICE_SET_VALUE,
            {ATTR_ENTITY_ID: [entity_id], ATTR_VALUE: 50},
            blocking=True,
        )
    assert mock.call_args[0] == snapshot

"""Switch tests for the Skybell integration."""

from contextlib import suppress
from unittest.mock import patch

import pytest
from syrupy.assertion import SnapshotAssertion

from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import ATTR_ENTITY_ID, SERVICE_TURN_OFF, SERVICE_TURN_ON
from homeassistant.core import HomeAssistant


@pytest.mark.parametrize(
    ("entity_id", "service"),
    [
        ("switch.front_door_do_not_disturb", SERVICE_TURN_ON),
        ("switch.front_door_do_not_ring", SERVICE_TURN_ON),
        ("switch.front_door_motion_sensor", SERVICE_TURN_OFF),
    ],
)
@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_switches(
    hass: HomeAssistant,
    setup_integration: None,
    snapshot: SnapshotAssertion,
    entity_id: str,
    service: str,
) -> None:
    """Test switch entities."""

    assert hass.states.get(entity_id) == snapshot

    patched = "homeassistant.components.skybell.api.device.SkybellDevice._set_setting"
    with suppress(AttributeError), patch(patched) as mock:
        await hass.services.async_call(
            SWITCH_DOMAIN,
            service,
            {ATTR_ENTITY_ID: [entity_id]},
            blocking=True,
        )
    assert list(mock.call_args) == snapshot

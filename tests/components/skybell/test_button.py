"""Button tests for the Skybell integration."""

from unittest.mock import patch

import pytest
from syrupy.assertion import SnapshotAssertion

from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN, SERVICE_PRESS
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant


@pytest.mark.parametrize(
    "entity_id",
    [
        "button.front_door_play_tone",
        "button.front_door_reboot",
    ],
)
@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_buttons(
    hass: HomeAssistant,
    setup_integration: None,
    snapshot: SnapshotAssertion,
    entity_id: str,
) -> None:
    """Test button entities."""
    assert hass.states.get("button.front_door_play_tone") == snapshot

    patched = "homeassistant.components.skybell.api.device.SkybellDevice._request"
    with patch(patched) as mock:
        await hass.services.async_call(
            BUTTON_DOMAIN,
            SERVICE_PRESS,
            {ATTR_ENTITY_ID: [entity_id]},
            blocking=True,
        )
    assert list(mock.call_args) == snapshot

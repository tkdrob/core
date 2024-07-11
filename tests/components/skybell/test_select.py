"""Select tests for the Skybell integration."""

from contextlib import suppress
from unittest.mock import patch

import pytest
from syrupy.assertion import SnapshotAssertion

from homeassistant.components.select import DOMAIN as SELECT_DOMAIN
from homeassistant.const import ATTR_ENTITY_ID, ATTR_OPTION, SERVICE_SELECT_OPTION
from homeassistant.core import HomeAssistant


@pytest.mark.parametrize(
    ("entity_id", "option"),
    [
        ("select.front_door_button_tone", "1950s mechanical doorbell"),
        ("select.front_door_image_quality", "medium"),
        ("select.front_door_live_volume", "high"),
        ("select.front_door_motion_chime_volume", "off"),
        ("select.front_door_motion_tone", "1950s mechanical doorbell"),
        ("select.front_door_outdoor_chime_volume", "high"),
        ("select.front_door_test_tone", "1950s mechanical doorbell"),
    ],
)
@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_selects(
    hass: HomeAssistant,
    setup_integration: None,
    snapshot: SnapshotAssertion,
    entity_id: str,
    option: str,
) -> None:
    """Test select entities."""

    assert hass.states.get(entity_id) == snapshot

    patched = "homeassistant.components.skybell.api.device.SkybellDevice._request"
    with suppress(AttributeError), patch(patched) as mock:
        await hass.services.async_call(
            SELECT_DOMAIN,
            SERVICE_SELECT_OPTION,
            {ATTR_ENTITY_ID: [entity_id], ATTR_OPTION: option},
            blocking=True,
        )
    assert list(mock.call_args) == snapshot

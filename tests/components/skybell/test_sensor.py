"""Sensor tests for the Skybell integration."""

import pytest
from syrupy.assertion import SnapshotAssertion

from homeassistant.core import HomeAssistant

SENSORS = [
    # "chime_level",
    "last_button_event",
    "last_motion_event",
    "last_check_in",
    # "motion_threshold",
    # "video_profile",
    "wi_fi_ssid",
    "wi_fi_status",
]


@pytest.mark.usefixtures("entity_registry_enabled_by_default")
async def test_sensors(
    hass: HomeAssistant, setup_integration: None, snapshot: SnapshotAssertion
) -> None:
    """Test sensors entities."""
    for name in SENSORS:
        state = hass.states.get(f"sensor.front_door_{name}")
        assert state == snapshot(name=state.entity_id)

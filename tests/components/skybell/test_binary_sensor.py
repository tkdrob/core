"""Binary sensor tests for the Skybell integration."""

from syrupy.assertion import SnapshotAssertion

from homeassistant.core import HomeAssistant


async def test_binary_sensors(
    hass: HomeAssistant, setup_integration: None, snapshot: SnapshotAssertion
) -> None:
    """Test binary sensor entities."""
    state = hass.states.get("binary_sensor.front_door_button")
    assert state == snapshot(name=state.entity_id)
    state = hass.states.get("binary_sensor.front_door_motion")
    assert state == snapshot(name=state.entity_id)

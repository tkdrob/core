"""Test Tautulli config flow."""
from unittest.mock import patch

from pytautulli import exceptions

from homeassistant import data_entry_flow, setup
from homeassistant.components.tautulli.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant

from . import (
    CONF_CONFIG_FLOW,
    CONF_DATA,
    NAME,
    _create_mocked_tautulli,
    _patch_config_flow_tautulli,
)

from tests.common import MockConfigEntry


def _patch_setup():
    return patch(
        "homeassistant.components.tautulli.async_setup_entry",
        return_value=True,
    )


async def test_form(hass: HomeAssistant) -> None:
    """Test we get the form."""
    await setup.async_setup_component(hass, "persistent_notification", {})
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result["errors"] == {}

    mocked_tautulli = await _create_mocked_tautulli(True)
    with _patch_config_flow_tautulli(
        mocked_tautulli
    ), _patch_setup() as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            CONF_CONFIG_FLOW,
        )
        await hass.async_block_till_done()

    assert result2["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result2["title"] == NAME
    assert result2["data"] == CONF_DATA
    assert len(mock_setup_entry.mock_calls) == 1


async def test_flow_user_already_configured(hass):
    """Test user initialized flow with duplicate server."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=CONF_CONFIG_FLOW,
    )

    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=CONF_CONFIG_FLOW
    )

    assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result["reason"] == "already_configured"


async def test_flow_user_cannot_connect(hass):
    """Test user initialized flow with unreachable server."""
    mocked_tautulli = await _create_mocked_tautulli(True)
    with _patch_config_flow_tautulli(mocked_tautulli) as tautullimock:
        tautullimock.side_effect = exceptions.ConnectionError
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONF_CONFIG_FLOW
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {"base": "cannot_connect"}


async def test_flow_user_unknown_error(hass):
    """Test user initialized flow with unreachable server."""
    mocked_tautulli = await _create_mocked_tautulli(True)
    with _patch_config_flow_tautulli(mocked_tautulli) as tautullimock:
        tautullimock.side_effect = Exception
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=CONF_CONFIG_FLOW
        )
        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {"base": "unknown"}

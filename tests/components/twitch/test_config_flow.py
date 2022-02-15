"""Test Twitch config flow."""
from unittest.mock import patch

from twitchio import errors

from homeassistant.components.twitch.const import DEFAULT_NAME, DOMAIN
from homeassistant.config_entries import SOURCE_REAUTH, SOURCE_USER
from homeassistant.const import CONF_API_KEY, CONF_API_TOKEN, CONF_SOURCE
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import (
    RESULT_TYPE_ABORT,
    RESULT_TYPE_CREATE_ENTRY,
    RESULT_TYPE_FORM,
)

from . import CONF_DATA, patch_twitch, create_entry, patch_twitch_users


def _patch_setup():
    return patch("homeassistant.components.twitch.async_setup_entry")


async def test_flow_user(hass: HomeAssistant):
    """Test user initialized flow."""
    with patch_twitch(), _patch_setup(), patch_twitch_users():
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={CONF_SOURCE: SOURCE_USER},
        )
        assert result["type"] == RESULT_TYPE_FORM
        assert result["step_id"] == "user"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=CONF_DATA,
        )
        assert result["type"] == RESULT_TYPE_CREATE_ENTRY
        assert result["title"] == DEFAULT_NAME
        assert result["data"] == CONF_DATA
        assert result["result"].unique_id == "4617940896"


#async def test_flow_user_cannot_connect(hass: HomeAssistant):
#    """Test user initialized flow with unreachable service."""
#    with patch_twitch() as twitchmock:
#        twitchmock.side_effect = errors.HTTPException
#        result = await hass.config_entries.flow.async_init(
#            DOMAIN, context={CONF_SOURCE: SOURCE_USER}, data=CONF_DATA
#        )
#        assert result["type"] == RESULT_TYPE_FORM
#        assert result["step_id"] == "user"
#        assert result["errors"]["base"] == "cannot_connect"


#async def test_flow_user_invalid_auth(hass: HomeAssistant):
#    """Test user initialized flow with invalid authentication."""
#    with patch_twitch() as twitchmock:
#        twitchmock.side_effect = errors.AuthenticationError
#        result = await hass.config_entries.flow.async_init(
#            DOMAIN, context={CONF_SOURCE: SOURCE_USER}, data=CONF_DATA
#        )
#        assert result["type"] == RESULT_TYPE_FORM
#        assert result["step_id"] == "user"
#       assert result["errors"]["base"] == "invalid_auth"


#async def test_flow_user_unknown(hass: HomeAssistant):
#    """Test user initialized flow with unknown error."""
#    with patch_twitch() as twitchmock:
#        twitchmock.side_effect = Exception
#        result = await hass.config_entries.flow.async_init(
#            DOMAIN, context={CONF_SOURCE: SOURCE_USER}, data=CONF_DATA
#        )
#        assert result["type"] == RESULT_TYPE_FORM
#        assert result["step_id"] == "user"
#        assert result["errors"]["base"] == "unknown"


#async def test_flow_reauth(hass: HomeAssistant):
#    """Test reauth step."""
#    entry = create_entry(hass)
#    with patch_twitch(), _patch_setup():
#        result = await hass.config_entries.flow.async_init(
#            DOMAIN,
#            context={
#                CONF_SOURCE: SOURCE_REAUTH,
#                "entry_id": entry.entry_id,
#                "unique_id": entry.unique_id,
#            },
#            data=CONF_DATA,
#        )

#        assert result["type"] == RESULT_TYPE_FORM
#        assert result["step_id"] == "user"

#        new_conf = {CONF_API_TOKEN: "1234567890"}
#        result = await hass.config_entries.flow.async_configure(
#            result["flow_id"],
#            user_input=new_conf,
#        )
#        assert result["type"] == RESULT_TYPE_ABORT
#        assert result["reason"] == "reauth_successful"
#        assert entry.data == new_conf

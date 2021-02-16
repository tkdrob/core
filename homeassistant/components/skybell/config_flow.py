"""Config flow for Skybell integration."""
from skybellpy import Skybell
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from . import DOMAIN  # pylint:disable=unused-import
from . import _LOGGER, AGENT_IDENTIFIER

DATA_SCHEMA = vol.Schema({"host": str, "name": str})


class SkybellFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Skybell."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        """Handle a flow initiated by the user."""
        errors = {}

        if user_input is not None:
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]

            if await self._async_endpoint_existed(username):
                return self.async_abort(reason="already_configured")

            try:
                await self._async_try_connect(username, password)
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=DOMAIN,
                    data={CONF_USERNAME: username, CONF_PASSWORD: password},
                )

        user_input = user_input or {}
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_USERNAME, default=user_input.get(CONF_USERNAME)
                    ): str,
                    vol.Required(
                        CONF_PASSWORD,
                        default=user_input.get(CONF_PASSWORD),
                    ): str,
                }
            ),
            errors=errors,
        )

    async def _async_endpoint_existed(self, endpoint):
        for entry in self._async_current_entries():
            if endpoint == entry.data.get(CONF_USERNAME):
                return True
        return False

    async def _async_try_connect(self, username, password):
        session = async_get_clientsession(self.hass)
        skybell = Skybell(
            session=session,
            loop=self.hass.loop,
            username=username,
            password=password,
            get_devices=True,
            cache_path="./skybell_cache.pickle",
            agent_identifier=AGENT_IDENTIFIER,
        )
        await skybell.get_devices()

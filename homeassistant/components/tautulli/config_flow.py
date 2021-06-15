"""Config flow for Tautulli."""
from __future__ import annotations

import copy
import logging
from typing import Any

from pytautulli import Tautulli, exceptions
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import (
    CONF_API_KEY,
    CONF_HOST,
    CONF_PATH,
    CONF_PORT,
    CONF_SSL,
    CONF_VERIFY_SSL,
)
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_MONITORED_USERS,
    DATA_KEY_API,
    DEFAULT_NAME,
    DEFAULT_VERIFY_SSL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class TautulliConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tautulli."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(entry):
        """Get the options flow for this handler."""
        return TautulliOptionsFlowHandler(entry)

    async def async_step_user(self, user_input=None):
        """Handle a flow initiated by the user."""
        errors = {}
        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]
            path = user_input[CONF_PATH]
            api_key = user_input[CONF_API_KEY]
            ssl = user_input[CONF_SSL]
            if CONF_VERIFY_SSL not in user_input:
                user_input[CONF_VERIFY_SSL] = DEFAULT_VERIFY_SSL
            verify_ssl = user_input[CONF_VERIFY_SSL]
            self._async_abort_entries_match({CONF_HOST: host})

            api, error = await self._async_try_connect(user_input)
            if error is None:
                await self.async_set_unique_id(api.tautulli_server_identity)
                self._abort_if_unique_id_configured(updates={CONF_HOST: host})
                return self.async_create_entry(
                    title=DEFAULT_NAME,
                    data={
                        CONF_API_KEY: api_key,
                        CONF_HOST: host,
                        CONF_PORT: port,
                        CONF_PATH: path,
                        CONF_SSL: ssl,
                        CONF_VERIFY_SSL: verify_ssl,
                    },
                )
            errors["base"] = error

        user_input = user_input or {}
        data_schema = {
            vol.Required(CONF_API_KEY, default=user_input.get(CONF_API_KEY) or ""): str,
            vol.Required(CONF_HOST, default=user_input.get(CONF_HOST) or ""): str,
            vol.Optional(CONF_PORT, default=user_input.get(CONF_PORT) or "8181"): str,
            vol.Optional(CONF_PATH, default=user_input.get(CONF_PATH) or ""): str,
            vol.Optional(CONF_SSL, default=user_input.get(CONF_SSL) or False): bool,
        }
        if self.show_advanced_options:
            data_schema[
                vol.Optional(
                    CONF_VERIFY_SSL, default=user_input.get(CONF_VERIFY_SSL) or True
                )
            ] = bool

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(data_schema),
            errors=errors or {},
        )

    async def async_step_import(self, import_config):
        """Import a config entry from configuration.yaml."""
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")
        return await self.async_step_user(import_config)

    async def _async_try_connect(self, user_input):
        """Try connecting to Tautulli."""
        try:
            api = Tautulli(
                user_input[CONF_HOST],
                user_input[CONF_PORT],
                user_input[CONF_API_KEY],
                self.hass.loop,
                async_get_clientsession(self.hass, user_input[CONF_VERIFY_SSL]),
                user_input[CONF_SSL],
                user_input[CONF_PATH],
            )
            await api.test_connection()
            await api.get_server_identity()
        except exceptions.ConnectError:
            _LOGGER.error("Error connecting to tautulli")
            return None, "cannot_connect"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            return None, "unknown"
        return api, None


class TautulliOptionsFlowHandler(OptionsFlow):
    """Config flow options for AccuWeather."""

    def __init__(self, entry: ConfigEntry) -> None:
        """Initialize Tautulli options flow."""
        self.options = copy.deepcopy(dict(entry.options))
        self.entry = entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user."""
        api = self.hass.data[DOMAIN][self.entry.entry_id][DATA_KEY_API]
        await api.get_users()
        if user_input is not None:
            account_data = {
                user: {"enabled": bool(user in user_input[CONF_MONITORED_USERS])}
                for user in api.tautulli_users
            }
            self.options[CONF_MONITORED_USERS] = account_data
            await self.hass.config_entries.async_reload(self.entry.entry_id)
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_MONITORED_USERS,
                        default=self.options[CONF_MONITORED_USERS],
                    ): cv.multi_select(api.tautulli_users),
                }
            ),
        )

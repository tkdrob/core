"""Config flow for Twitch integration."""
from __future__ import annotations

from copy import deepcopy
import logging
from typing import Any

from aiohttp.client_exceptions import ClientConnectorError
from twitchio import Client, errors
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_API_TOKEN, CONF_NAME, CONF_TOKEN, Platform
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.typing import ConfigType

from .const import CONF_CHANNELS, DEFAULT_NAME, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def validate_input(user_input: dict) -> tuple[dict[str, str] | None, str | None]:
    """Handle common flow input validation."""
    api = Client(user_input[CONF_API_TOKEN])
    try:
        await api.validate()
    except (errors.HTTPException, ClientConnectorError):
        return {"base": "cannot_connect"}, None
    except errors.AuthenticationError:
        return {"base": "invalid_auth"}, None
    except Exception:  # pylint:disable=broad-except
        return {"base": "unknown"}, None
    return None, api.user_id


class TwitchFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Twitch."""

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        """Get the options flow for this handler."""
        return TwitchOptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initiated by the user."""
        errors: dict[str, str] | None = {}
        if user_input is not None:
            errors, id = await validate_input(user_input)
            if errors is None:
                entry = await self.async_set_unique_id(id)
                if entry and self.source == config_entries.SOURCE_REAUTH:
                    self.hass.config_entries.async_update_entry(entry, data=user_input)
                    await self.hass.config_entries.async_reload(entry.entry_id)
                    return self.async_abort(reason="reauth_successful")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input.get(CONF_NAME, DEFAULT_NAME),
                    data={CONF_API_TOKEN: user_input[CONF_API_TOKEN]},
                )
        user_input = user_input or {}
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_API_TOKEN, default=user_input.get(CONF_API_TOKEN) or ""
                    ): str,
                }
            ),
            errors=errors,
        )

    async def async_step_import(self, import_config: ConfigType) -> FlowResult:
        """Import a config entry from configuration.yaml."""
        _msg = "Twitch yaml config in now deprecated and has been imported if a token was specified. Please verify successful import before removing it"
        _LOGGER.warning(_msg)
        if CONF_TOKEN not in import_config:
            _LOGGER.error(
                "Twitch now requires a token to access their api. Please refer to the Twitch integration documentation to obtain one"
            )
        else:
            for entry in self._async_current_entries():  # TODO
                if entry.data[CONF_API_TOKEN] == import_config[CONF_TOKEN]:
                    return self.async_abort(reason="already_configured")
        return await self.async_step_user(
            {CONF_API_TOKEN: import_config.get(CONF_TOKEN, "")}
        )

    async def async_step_reauth(self, config: dict[str, Any]) -> FlowResult:
        """Handle a reauthorization flow request."""
        return await self.async_step_user()


class TwitchOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Twitch client options."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.entry = entry
        self.options = deepcopy(dict(entry.options))

    async def async_step_init(
        self, user_input: dict[str, int] | None = None
    ) -> FlowResult:
        """Manage Twitch options."""
        if user_input is None:
            api: Client = self.hass.data[DOMAIN][self.entry.entry_id]
            try:
                _ch = (await api.search_channels(api.nick))[0]
                follows = await _ch.fetch_following()
                users = [u.to_user.name.lower() for u in follows]
            except Exception:  # pylint:disable=broad-except
                users = self.options[CONF_CHANNELS]
            for user in users:
                if user not in self.options[CONF_CHANNELS]:
                    self.options[CONF_CHANNELS][user] = {"enabled": True}
            for user in [
                user
                for user in self.options[CONF_CHANNELS]
                if user not in users
                and not self.options[CONF_CHANNELS][user]["enabled"]
            ]:
                del self.options[CONF_CHANNELS][user]
        else:
            await self.hass.config_entries.async_unload(self.entry.entry_id)
            entity_registry = er.async_get(self.hass)
            for user in self.options[CONF_CHANNELS]:
                if (
                    self.options[CONF_CHANNELS][user]["enabled"]
                    and user not in user_input[CONF_CHANNELS]
                ):
                    entity_id = entity_registry.async_get_entity_id(
                        Platform.SENSOR, DOMAIN, f"{user}_{self.entry.entry_id}"
                    )
                    entity_registry.async_remove(entity_id)
            channel_data = {
                CONF_CHANNELS: {
                    user: {"enabled": bool(user in user_input[CONF_CHANNELS])}
                    for user in self.options[CONF_CHANNELS]
                }
            }
            await self.hass.config_entries.async_reload(self.entry.entry_id)
            return self.async_create_entry(title="", data=channel_data)
        options = {
            vol.Required(
                CONF_CHANNELS,
                default={
                    user
                    for user in self.options[CONF_CHANNELS]
                    if self.options[CONF_CHANNELS][user]["enabled"]
                },
            ): cv.multi_select([user for user in self.options[CONF_CHANNELS]]),
        }

        return self.async_show_form(step_id="init", data_schema=vol.Schema(options))

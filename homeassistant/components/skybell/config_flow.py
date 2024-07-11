"""Config flow for Skybell integration."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import Client, exceptions
from .const import DOMAIN


class SkybellFlowHandler(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Skybell."""

    MINOR_VERSION = 2

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle a reauthorization flow request."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, str] | None = None
    ) -> ConfigFlowResult:
        """Handle user's reauth credentials."""
        errors = {}
        entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        assert entry
        email = entry.data[CONF_EMAIL]
        if user_input:
            password = user_input[CONF_PASSWORD]
            try:
                skybell = await self._async_validate_input(email, password)
            except InputValidationError as ex:
                errors["base"] = ex.base
            else:
                self.hass.config_entries.async_update_entry(
                    entry,
                    data=skybell.auth.dict(),
                )
                await self.hass.config_entries.async_reload(entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): str}),
            description_placeholders={CONF_EMAIL: email},
            errors=errors,
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initiated by the user."""
        errors = {}

        if user_input is not None:
            email = user_input[CONF_EMAIL].lower()
            password = user_input[CONF_PASSWORD]

            self._async_abort_entries_match({CONF_EMAIL: email})
            try:
                skybell = await self._async_validate_input(email, password)
            except InputValidationError as ex:
                errors["base"] = ex.base
            else:
                data = skybell.auth.dict() | user_input
                await self.async_set_unique_id(skybell.user.account_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=email, data=data)

        user_input = user_input or {}
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EMAIL, default=user_input.get(CONF_EMAIL)): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

    async def _async_validate_input(self, email: str, password: str) -> Client:
        """Validate login credentials."""
        skybell = Client(
            username=email,
            password=password,
            session=async_get_clientsession(self.hass),
        )
        try:
            await skybell.initialize()
        except exceptions.SkybellAuthenticationException as ex:
            raise InputValidationError("invalid_auth") from ex
        except exceptions.SkybellException as ex:
            raise InputValidationError("cannot_connect") from ex
        except Exception as ex:
            raise InputValidationError("unknown") from ex
        return skybell


class InputValidationError(HomeAssistantError):
    """Error to indicate we cannot proceed due to invalid input."""

    def __init__(self, base: str) -> None:
        """Initialize with error base."""
        super().__init__()
        self.base = base

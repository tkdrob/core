"""Tests for the Tautulli integration."""

from unittest.mock import AsyncMock, patch

from homeassistant.components.tautulli.const import CONF_MONITORED_USERS
from homeassistant.const import (
    CONF_API_KEY,
    CONF_HOST,
    CONF_PATH,
    CONF_PORT,
    CONF_SSL,
    CONF_VERIFY_SSL,
)

API_KEY = "abcd"
HOST = "1.2.3.4"
NAME = "Tautulli"
PORT = "8181"
PATH = ""
SSL = False
VERIFY_SSL = True

CONF_DATA = {
    CONF_API_KEY: API_KEY,
    CONF_HOST: HOST,
    CONF_PORT: PORT,
    CONF_PATH: PATH,
    CONF_SSL: SSL,
    CONF_VERIFY_SSL: VERIFY_SSL,
}

CONF_CONFIG_FLOW = {
    CONF_API_KEY: API_KEY,
    CONF_HOST: HOST,
    CONF_PORT: PORT,
    CONF_PATH: PATH,
    CONF_SSL: SSL,
}
AVAILABLE_USERS = ["foo", "bar"]

CONF_OPTIONS_FLOW = {}
CONF_OPTIONS_FLOW[CONF_MONITORED_USERS] = AVAILABLE_USERS


async def _create_mocked_tautulli(raise_exception=False):
    mocked_tautulli = AsyncMock()
    mocked_tautulli.tautulli_users = AsyncMock()
    return mocked_tautulli


def _patch_init_tautulli(mocked_tautulli):
    return patch(
        "homeassistant.components.tautulli.Tautulli", return_value=mocked_tautulli
    )


def _patch_config_flow_tautulli(mocked_tautulli):
    return patch(
        "homeassistant.components.tautulli.config_flow.Tautulli",
        return_value=mocked_tautulli,
    )

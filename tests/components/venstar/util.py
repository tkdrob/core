"""Tests for the venstar integration."""

from unittest.mock import patch

import requests_mock

from homeassistant.components.venstar.const import DOMAIN
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PIN,
    CONF_SSL,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry, load_fixture

TEST_MODELS = ["t2k", "colortouch"]

TEST_DATA = {
    CONF_HOST: "1.1.1.1",
    CONF_USERNAME: "test-username",
    CONF_PASSWORD: "test-password",
    CONF_PIN: "test-pin",
    CONF_SSL: False,
}


def mock_venstar_devices(f):
    """Decorate function to mock a Venstar Colortouch and T2000 thermostat API."""

    async def wrapper(hass):
        # Mock thermostats are:
        # Venstar T2000, FW 4.38
        # Venstar "colortouch" T7850, FW 5.1
        with requests_mock.mock() as m:
            for model in TEST_MODELS:
                m.get(
                    f"http://venstar-{model}.localdomain/",
                    text=load_fixture(f"venstar/{model}_root.json"),
                )
                m.get(
                    f"http://venstar-{model}.localdomain/query/info",
                    text=load_fixture(f"venstar/{model}_info.json"),
                )
                m.get(
                    f"http://venstar-{model}.localdomain/query/sensors",
                    text=load_fixture(f"venstar/{model}_sensors.json"),
                )
                m.get(
                    f"http://venstar-{model}.localdomain/query/alerts",
                    text=load_fixture(f"venstar/{model}_alerts.json"),
                )
            return await f(hass)

    return wrapper


async def async_init_integration(
    hass: HomeAssistant,
    platform: str,
    model: str,
    skip_setup: bool = False,
):
    """Set up the venstar integration in Home Assistant."""
    entry = create_entry(hass, model)
    if not skip_setup:
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    with patch("homeassistant.components.venstar.PLATFORMS", [platform]):
        await async_setup_component(hass, DOMAIN, {})
        await hass.async_block_till_done()


def create_entry(hass: HomeAssistant, model: str):
    """Add config entry in Home Assistant."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: f"venstar-{model}.localdomain",
            CONF_SSL: False,
        },
    )
    entry.add_to_hass(hass)

    return entry

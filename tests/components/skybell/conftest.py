"""Configure pytest for Skybell tests."""

from http import HTTPStatus

from aiohttp.hdrs import CONTENT_TYPE
import pytest

from homeassistant.components.skybell.const import DOMAIN
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONTENT_TYPE_JSON
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry, load_fixture
from tests.test_util.aiohttp import AiohttpClientMocker

EMAIL = "test@example.com"
PASSWORD = "password"
BASE_URL = "https://api.skybell.network/api/v5/"
COGNITO_URL = "https://cognito-idp.us-east-2.amazonaws.com"

CONF_AUTH_FLOW = {
    CONF_EMAIL: EMAIL,
    CONF_PASSWORD: PASSWORD,
}

CONF_DATA = {
    CONF_EMAIL: EMAIL,
    CONF_PASSWORD: PASSWORD,
    "AccessToken": "1234",
    "ExpiresAt": 1685543400.0,
    "ExpiresIn": 3600,
    "IdToken": "secret",
    "RefreshToken": "5678",
    "TokenType": "Bearer",
}


@pytest.fixture(name="connection")
def mock_connection(aioclient_mock: AiohttpClientMocker) -> None:
    """Set AioClient responses."""
    aioclient_mock.post(
        COGNITO_URL,
        text=load_fixture("skybell/auth.json"),
        headers={CONTENT_TYPE: CONTENT_TYPE_JSON},
    )
    aioclient_mock.get(
        f"{BASE_URL}user",
        text=load_fixture("skybell/user.json"),
        headers={CONTENT_TYPE: CONTENT_TYPE_JSON},
    )
    aioclient_mock.get(
        f"{BASE_URL}shares",
        text=load_fixture("skybell/shares.json"),
        headers={CONTENT_TYPE: CONTENT_TYPE_JSON},
    )
    aioclient_mock.get(
        f"{BASE_URL}devices",
        text=load_fixture("skybell/devices.json"),
        headers={CONTENT_TYPE: CONTENT_TYPE_JSON},
    )
    aioclient_mock.get(
        f"{BASE_URL}devices/12345679-1234-1234-1234-123456789012",
        text=load_fixture("skybell/device.json"),
        headers={CONTENT_TYPE: CONTENT_TYPE_JSON},
    )
    aioclient_mock.get(
        f"{BASE_URL}activity/summary",
        text=load_fixture("skybell/activity_summary.json"),
        params={"device": "12345679-1234-1234-1234-123456789012"},
        headers={CONTENT_TYPE: CONTENT_TYPE_JSON},
    )
    aioclient_mock.get(
        f"{BASE_URL}activity",
        text=load_fixture("skybell/activity.json"),
        headers={CONTENT_TYPE: CONTENT_TYPE_JSON},
    )
    aioclient_mock.get(
        f"{BASE_URL}tones",
        text=load_fixture("skybell/tones.json"),
        headers={CONTENT_TYPE: CONTENT_TYPE_JSON},
    )


@pytest.fixture
def cannot_connect(aioclient_mock: AiohttpClientMocker) -> None:
    aioclient_mock.post(COGNITO_URL, status=HTTPStatus.INTERNAL_SERVER_ERROR)


@pytest.fixture
def invalid_auth(aioclient_mock: AiohttpClientMocker) -> None:
    aioclient_mock.post(
        COGNITO_URL,
        status=HTTPStatus.BAD_REQUEST,
    )


@pytest.fixture
def unknown_error(aioclient_mock: AiohttpClientMocker) -> None:
    aioclient_mock.post(COGNITO_URL, exc=Exception)


@pytest.fixture(name="config_entry")
def mock_config_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Create Skybell entry in Home Assistant."""
    return MockConfigEntry(
        domain=DOMAIN,
        data=CONF_DATA,
        unique_id="12345678-1234-1234-1234-123456789012",
        title=EMAIL,
    )


@pytest.fixture(name="setup_integration")
async def mock_setup_integration(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    connection: None,
) -> None:
    """Set up the integration in Home Assistant."""
    config_entry.add_to_hass(hass)
    assert await async_setup_component(hass, DOMAIN, {})
    await hass.async_block_till_done()

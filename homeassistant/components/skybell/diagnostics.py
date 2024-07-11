"""Support for Skybell diagnostics."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics.util import async_redact_data
from homeassistant.core import HomeAssistant

from .coordinator import SkybellConfigEntry

TO_REDACT_ACT = [
    "account_id",
    "activity_id",
    "device_id",
    "events",
    "image",
    "video_url",
]

TO_REDACT_CONFIG = ["data", "title", "unique_id"]

TO_REDACT_DEVICES = [
    "account_id",
    "certificate_id",
    "client_id",
    "device_id",
    "invite_token",
    "ip_address_public",
    "serial_number",
]

TO_REDACT_SHARES = [
    "client_id",
    "invite_token",
    "invited_email",
    "share_id",
    "shared_device_id",
    "shared_to_account_id",
    "sharing_account_id",
]

TO_REDACT_USER = ["account_id", "email", "hd_user_id"]


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: SkybellConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    client = entry.runtime_data.client

    return {
        "activities": [
            async_redact_data(i.dict(), TO_REDACT_ACT) for i in client.activities
        ],
        "config_entry": async_redact_data(entry.as_dict(), TO_REDACT_CONFIG),
        "devices": [
            async_redact_data(i.info.dict(), TO_REDACT_DEVICES) for i in client.devices
        ],
        "shares": [
            async_redact_data(i.dict(), TO_REDACT_SHARES) for i in client.shares
        ],
        "user": async_redact_data(client.user.dict(), TO_REDACT_USER),
    }

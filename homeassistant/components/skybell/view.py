"""Implement a view to provide proxied Skybell thumbnails to the media browser."""

from __future__ import annotations

from collections.abc import Mapping
from http import HTTPStatus

from aiohttp import web
from aiohttp.hdrs import CACHE_CONTROL

from homeassistant.components.http import KEY_AUTHENTICATED, HomeAssistantView
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import Unauthorized

from .const import DOMAIN
from .coordinator import SkybellConfigEntry


class SkybellImageView(HomeAssistantView):
    """Media player view to serve a Skybell image."""

    name = "api:skybell:image"
    url = "/api/skybell_image_proxy/{unique_id}/{media_content_id}"

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the media view."""
        self.hass = hass

    async def get(
        self,
        request: web.Request,
        unique_id: str,
        media_content_id: str,
    ) -> web.Response:
        """Start a get request."""
        if not request[KEY_AUTHENTICATED]:
            raise Unauthorized

        entry: SkybellConfigEntry | None = (
            self.hass.config_entries.async_entry_for_domain_unique_id(DOMAIN, unique_id)
        )
        if not entry or entry.state is not ConfigEntryState.LOADED:
            return web.Response(status=HTTPStatus.NOT_FOUND)

        activities = entry.runtime_data.client.activities_dict
        if not (activity := activities.get(media_content_id)):
            return web.Response(status=HTTPStatus.NOT_FOUND)

        headers: Mapping = {CACHE_CONTROL: "max-age=3600"}
        return web.Response(
            body=activity.image, content_type="image/jpg", headers=headers
        )

"""Skybell Media Source Implementation."""

from __future__ import annotations

from datetime import date, timedelta

from homeassistant.components.media_player import MediaClass
from homeassistant.components.media_source import BrowseError
from homeassistant.components.media_source.models import (
    BrowseMediaSource,
    MediaSource,
    MediaSourceItem,
    MediaType,
    PlayMedia,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.util.dt import as_local

from .api import Client
from .const import DEFAULT_NAME, DOMAIN
from .coordinator import SkybellConfigEntry
from .view import SkybellImageView


async def async_get_media_source(hass: HomeAssistant) -> SkybellSource:
    """Set up Skybell media source."""
    entries = hass.config_entries.async_entries(
        DOMAIN, include_disabled=False, include_ignore=False
    )
    hass.http.register_view(SkybellImageView(hass))
    return SkybellSource(hass, entries)


class SkybellSource(MediaSource):
    """Provide Skybell screenshots and videos as media sources."""

    name: str = "Skybell Media"

    def __init__(self, hass: HomeAssistant, entries: list[SkybellConfigEntry]) -> None:
        """Initialize source."""
        super().__init__(DOMAIN)
        self.hass = hass
        self.entries = {entry.unique_id: entry for entry in entries}

    async def async_resolve_media(self, item: MediaSourceItem) -> PlayMedia:
        """Resolve media to a url."""
        unique_id, activity_id = item.identifier.split("/")
        client = self.entries[unique_id].runtime_data.client
        return PlayMedia(await client.get_activity_video_url(activity_id), "video/mp4")

    async def async_browse_media(self, item: MediaSourceItem) -> BrowseMediaSource:
        """Return media."""
        if all(
            entry.state is not ConfigEntryState.LOADED
            for entry in self.entries.values()
        ):
            raise BrowseError("No Skybell entries loaded")
        if not item.identifier:
            return BrowseMediaSource(
                domain=DOMAIN,
                identifier=DEFAULT_NAME,
                media_class=MediaClass.DIRECTORY,
                media_content_type=MediaType.VIDEO,
                title="Skybell Media",
                can_play=False,
                can_expand=True,
                children_media_class=MediaClass.DIRECTORY,
                children=await self._async_build_doorbells(item),
            )
        if entry := self.entries.get(item.identifier):
            client = entry.runtime_data.client
            return BrowseMediaSource(
                domain=DOMAIN,
                identifier=item.identifier,
                media_class=MediaClass.DIRECTORY,
                media_content_type=MediaType.VIDEO,
                title=f"{DEFAULT_NAME} {client.user.email}",
                can_play=False,
                can_expand=True,
                children=await _build_day_folders(item, client),
                children_media_class=MediaClass.VIDEO,
            )
        unique_id, day = item.identifier.split("/")
        client = self.entries[unique_id].runtime_data.client
        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=item.identifier,
            media_class=MediaClass.DIRECTORY,
            media_content_type=MediaType.VIDEO,
            title=f"{DEFAULT_NAME} {client.user.email} {day}",
            can_play=False,
            can_expand=True,
            children=await _build_video_response(unique_id, day, client),
            children_media_class=MediaClass.VIDEO,
        )

    async def _async_build_doorbells(
        self, item: MediaSourceItem
    ) -> list[BrowseMediaSource]:
        """Handle browsing different doorbells."""
        return [
            BrowseMediaSource(
                domain=DOMAIN,
                identifier=entry.unique_id,
                media_class=MediaClass.DIRECTORY,
                media_content_type=MediaClass.VIDEO,
                title=entry.title,
                can_play=False,
                can_expand=True,
            )
            for entry in self.entries.values()
        ]


async def _build_day_folders(
    item: MediaSourceItem, client: Client
) -> list[BrowseMediaSource]:
    return [
        BrowseMediaSource(
            domain=DOMAIN,
            identifier=f"{item.identifier}/{activity.activity_day}",
            media_class=MediaClass.DIRECTORY,
            media_content_type=MediaType.VIDEO,
            title=f"{activity.activity_day} ({activity.event_count})",
            can_play=False,
            can_expand=True,
        )
        for activity in await client.get_activity_summary()
    ]


async def _build_video_response(
    unique_id: str, day: str, client: Client
) -> list[BrowseMediaSource]:
    start = date.fromisoformat(day)
    return [
        BrowseMediaSource(
            domain=DOMAIN,
            identifier=f"{unique_id}/{event.activity_id}",
            media_class=MediaClass.VIDEO,
            media_content_type=MediaType.VIDEO,
            title=f"{event.device_name} {as_local(event.created_at).strftime("%H:%M:%S")}",
            can_play=event.video_ready,
            can_expand=False,
            thumbnail=get_proxy_image_url(unique_id, event.activity_id),
        )
        for event in await client.get_activity(
            start=start, end=start + timedelta(days=1)
        )
    ]


def get_proxy_image_url(
    unique_id: str,
    media_content_id: str,
) -> str:
    """Generate an url for a Skybell media browser image."""
    return f"/api/skybell_image_proxy/{unique_id}/{media_content_id}"

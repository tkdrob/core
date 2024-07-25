"""Device support for AIOSkybell."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, UTC
from enum import Enum
import time
from typing import TYPE_CHECKING, Any

from .const import LOGGER, EventType, HTTPMethod, ToneType
from .exceptions import SkybellException
from .models import (
    Activity,
    ChangeableMotionSettings,
    ChangeableSettings,
    DeviceInfo,
    Settings,
    Snapshot,
)

if TYPE_CHECKING:
    from . import Client


class RateLimiter:
    """Rate limiter."""

    def __init__(self) -> None:
        """Initialize the rate limiter."""
        self.interval = 30
        self.last_execution = 0.0

    def __call__(self, func: Callable) -> Callable:  # noqa: D102
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_time = time.time()
            if current_time - self.last_execution < self.interval:
                LOGGER.debug("Rate limit exceeded. Please wait %s", self.interval)
                return None
            result = func(*args, **kwargs)
            self.last_execution = current_time
            return result

        return wrapper


limit = RateLimiter()


class SkybellDevice:
    """Class for a Skybell device."""

    def __init__(self, client: Client, info: DeviceInfo) -> None:
        """Initialize."""
        self._client = client
        self.info = info
        self.activities: tuple[Activity, ...] = ()
        self.snapshot: Snapshot | None = None

    async def _request(self, path: str, **kwargs: dict[str, Any]) -> Any:
        """Send request with client session."""
        return await self._client._request(path, **kwargs)  # noqa: SLF001

    async def async_update(self) -> DeviceInfo:
        """Get the latest device information."""
        if info := await self._client.get_device_info(self.info):
            self.info = info
        return self.info

    async def async_get_events(self) -> tuple[Activity, ...]:
        """Get all events available for the device."""
        if days := await self._client.get_activity_summary(self):
            self.activities = await self._client.fetch_latest_activities(
                start=days[-1].activity_day, end=datetime.now(tz=UTC), device=self
            )
        return self.activities

    @limit
    async def get_snapshot(self) -> Snapshot | None:
        """Get a snapshot from a device."""
        try:
            res = await self._request(f"devices/{self.info.device_id}/snapshot")
        except SkybellException:
            res = None
            LOGGER.warning("Failed to get snapshot")
        if res and (data := res.get("data")):
            self.snapshot = Snapshot(**data)
        return self.snapshot

    async def _set_setting(self, json: Any) -> Any:
        return await self._request(
            f"devices/{self.info.device_id}/settings",
            json=json,
            method=HTTPMethod.POST,
        )

    async def set_settings(
        self, options: ChangeableSettings | ChangeableMotionSettings
    ) -> Settings:
        """Change settings on the device using the pydantic models."""
        res = await self._set_setting(options.dict(exclude_unset=True))
        data = self.info.settings.dict() | res["data"]
        self.info.settings = Settings(**data)  # type:ignore[misc]
        return self.info.settings

    async def set_tone(self, tone: str, tone_type: ToneType | str) -> Settings | None:
        """Set a tone for the type of event to be used."""
        _type = ToneType(tone_type)
        if tone == "Default tone":
            if _type is ToneType.MOTION:
                data = ChangeableSettings(chime_file_motion="")
            elif _type is ToneType.BUTTON:
                data = ChangeableSettings(chime_file="")
            else:
                raise ValueError(f"Invalid option {tone} for {_type}")
            return await self.set_settings(data)
        await self._request(
            f"devices/{self.info.device_id}/tone",
            json={"tone_type": _type, "tone_file": self._client.all_tones[tone]},
            method=HTTPMethod.POST,
        )
        return None

    async def play_tone(self) -> dict[str, str]:
        """Play the currently set test ring tone on the device."""
        return await self._request(  # type:ignore[no-any-return]
            f"devices/{self.info.device_id}/testtone",
            json={"file_name": "user_test.wav"},
            method=HTTPMethod.POST,
        )

    async def reboot(self) -> None:
        """Reboot the device."""
        await self._request(
            f"devices/{self.info.device_id}/reboot",
            method=HTTPMethod.POST,
        )

    async def get_signals(self) -> dict[str, Any]:
        """Start video stream."""
        res = await self._request(f"devices/signalling/{self.info.device_id}")
        return res["data"]  # type:ignore[no-any-return]

    async def fetch_latest_activities(self, **kwargs: dict[str, Any]) -> tuple[Activity, ...]:
        """Get the latest activities for this devices based on given criteria."""
        return await self._client.fetch_latest_activities(device=self, **kwargs)

    async def fetch_latest_activity(self, **kwargs: dict[str, Any]) -> Activity | None:
        """Get the latest activity for this devices."""
        activities = await self._client.fetch_latest_activities(device=self, **kwargs)
        return latest(activities, device=self)

    def latest_activity_datetime(
        self, type: EventType | None = None
    ) -> datetime | None:
        """Get the latest activity datetime for this device for the specified type."""
        if activity := self._client.latest_activity(type=type, device=self):
            return activity.created_at
        return None

    async def share(self, email: str) -> str:
        """Share this device with another account. Returns the invite token."""
        res = await self._request(
            f"devices/{self.info.device_id}/share",
            json={"invitedEmail": email},
            method=HTTPMethod.POST,
        )
        return res["data"]["invite_token"]  # type:ignore[no-any-return]

    @property
    def client(self) -> Client:
        """Return the client object."""
        return self._client


def latest(
    activities: tuple[Activity, ...],
    event_type: str | EventType | None = None,
    device: SkybellDevice | None = None,
) -> Activity | None:
    """Get the latest activity for the specified type. Use get_activity for newer activities."""
    _latest: Activity | None = None
    if event_type and not isinstance(event_type, Enum):
        event_type = EventType[event_type.upper()]
    for activity in activities:
        if device and activity.device_id != device.info.device_id:
            continue
        if (not event_type or event_type is activity.event_type) and (
            not _latest or activity.created_at > _latest.created_at
        ):
            _latest = activity
    return _latest

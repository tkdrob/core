"""API library for the Skybell Gen 5 mobile app."""

from __future__ import annotations

from datetime import date, datetime, time as dt_time, timedelta
from functools import cached_property
import time
from types import MappingProxyType
from typing import Any, Self
from zoneinfo import ZoneInfo

from aiohttp import ClientSession, hdrs
from aiohttp.client import ClientTimeout
from aiohttp.client_exceptions import ClientResponseError
import orjson

from .const import (
    BASE_URL,
    CLOCK_LEEWAY,
    DEFAULT_HEADERS,
    JSON,
    LOGGER,
    EventType,
    HTTPMethod,
)
from .device import SkybellDevice, latest
from .exceptions import SkybellAuthenticationException, SkybellException
from .models import (
    Activity,
    ActivityDetails,
    ActivitySummary,
    Auth,
    DeviceInfo,
    MotionRule,
    Share,
    Tone,
    User,
    dumps,
)


class Client:
    """Main Skybell class."""

    _close_session = False

    def __init__(
        self,
        username: str | None = None,
        password: str | None = None,
        auth: MappingProxyType[str, Any] | None = None,
        session: ClientSession | None = None,
        tzinfo: ZoneInfo | None = None,
    ) -> None:
        """Initialize Skybell object."""
        if not auth and (not username or not password):
            raise ValueError("Username and password is required")
        if session is None:
            session = ClientSession(json_serialize=dumps)
            self._close_session = True
        if tzinfo:
            DEFAULT_HEADERS["tz"] = tzinfo.key
        self._session = session
        self._username = username
        self._password = password
        self._auth = Auth(**auth) if auth else None
        self._rq_etags: dict[str, str] = {}
        self._shared_devices_info: dict[str, DeviceInfo] = {}
        self.devices: tuple[SkybellDevice, ...] = ()
        self.shares: tuple[Share, ...] = ()
        self.tones: dict[str, str] = {}
        self._user: User | None = None
        self.activitySummary: tuple[ActivitySummary, ...] = ()

    async def __aenter__(self) -> Self:
        """Async enter."""
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        """Async exit."""
        if self._session and self._close_session:
            await self._session.close()

    async def _request(
        self,
        path: str,
        method: HTTPMethod = HTTPMethod.GET,
        retry: bool = True,
        fresh: bool = False,
        **kwargs: Any,
    ) -> Any:
        if not self.valid_token:
            await self.authenticate()

        _headers = DEFAULT_HEADERS | {hdrs.AUTHORIZATION: self.auth.IdToken}
        if all([method is HTTPMethod.GET, not fresh, etag := self._rq_etags.get(path)]):
            _headers[hdrs.IF_NONE_MATCH] = etag  # type:ignore[assignment]
        res = await self._session.request(
            method=method.value,
            url=BASE_URL.joinpath(path),
            headers=_headers,
            timeout=ClientTimeout(10),
            **kwargs,
        )
        LOGGER.debug(res)
        LOGGER.debug(kwargs)
        if res.status == 599 and retry:
            return await self._request(path, method, False, fresh, **kwargs)
        try:
            res.raise_for_status()
        except ClientResponseError as ex:
            raise SkybellException(ex) from ex
        if (
            method is HTTPMethod.GET
            and "video" not in path
            and (etag := res.headers.get(hdrs.ETAG))
        ):
            self._rq_etags[path] = etag
        if res.content_type == JSON:
            res_json = await res.json()
            LOGGER.debug(res_json)
            return res_json
        if res.content_type == "text/plain":
            return await res.text()
        return None

    async def initialize(self) -> tuple[SkybellDevice, ...]:
        """Initialize."""
        if not self._auth:
            await self.authenticate()
        await self.get_user()
        await self.get_shares()
        self.tones = {t.name: t.file for t in await self.get_tones()}
        self.devices = tuple(
            [
                SkybellDevice(self, await self.get_device_info(device))
                for device in (await self.get_devices()).values()
            ]
        )
        return self.devices

    async def authenticate(self, _reauth: bool = False) -> None:
        """Get a new access token."""
        _headers = {
            hdrs.ACCEPT_ENCODING: "gzip",
            hdrs.CACHE_CONTROL: "no-store",
            hdrs.CONNECTION: hdrs.KEEP_ALIVE,
            hdrs.CONTENT_TYPE: "application/x-amz-json-1.1",
        }
        headers = _headers | {
            hdrs.USER_AGENT: "okhttp/4.9.2",
            "x-amz-target": "AWSCognitoIdentityProviderService.InitiateAuth",
        }
        json: dict[str, Any] = {"ClientId": "3r496699fhfl3vl79o4a41sm4b"}
        if self._auth and not _reauth:
            json = json | {
                "AuthFlow": "REFRESH_TOKEN_AUTH",
                "AuthParameters": {"REFRESH_TOKEN": self.auth.RefreshToken},
            }
        else:
            json = json | {
                "AuthFlow": "USER_PASSWORD_AUTH",
                "AuthParameters": {
                    "USERNAME": self._username,
                    "PASSWORD": self._password,
                },
                "ClientMetadata": {},
            }
        res = await self._session.post(
            "https://cognito-idp.us-east-2.amazonaws.com",
            headers=headers,
            json=json,
        )
        if res.status == 400:
            if not _reauth and self._auth and self._auth.email and self._auth.password:
                return await self.authenticate(True)
            raise SkybellAuthenticationException
        try:
            res.raise_for_status()
        except ClientResponseError as ex:
            raise SkybellException(ex) from ex
        auth = orjson.loads(await res.text())["AuthenticationResult"]
        auth = auth | {"ExpiresAt": auth["ExpiresIn"] + time.time() + CLOCK_LEEWAY}
        if self._auth:
            auth = {"RefreshToken": self.auth.RefreshToken} | auth
        self._auth = Auth(**auth)

    @property
    def valid_token(self) -> bool:
        """Return True if token is still valid."""
        return self.auth.ExpiresAt > time.time()

    async def get_user(self) -> User:
        """Get information on the signed in user."""
        if res := await self._request("user"):
            self._user = User(**res["data"])
        return self.user

    async def get_status(self) -> dict[str, Any]:
        """Get the status of the API."""
        return await self._request("status", fresh=True)  # type:ignore[no-any-return]

    async def get_shares(self) -> tuple[Share, ...]:
        """Get all access sharing details."""
        if res := await self._request("shares"):
            self.shares = tuple(Share(**i) for i in res["data"])
        return self.shares

    async def get_devices(self) -> dict[str, DeviceInfo]:
        """Get information on devices available to the signed in user."""
        if res := await self._request("devices"):
            devices = [DeviceInfo(**i) for i in res["data"]["rows"]]
            self._shared_devices_info = {d.device_id: d for d in devices}
        return self._shared_devices_info

    async def get_device_info(self, info: DeviceInfo) -> DeviceInfo:
        """Get the latest device info with telemetry."""
        _id = info.device_id
        if res := await self._request(f"devices/{_id}"):
            # device access permissions are not currently included in normal API call
            r_only = self._shared_devices_info[_id].shared_read_only
            return DeviceInfo(**res["data"], shared_read_only=r_only)
        return info

    async def get_rules(self) -> dict[str, Any]:
        """Get rules used by the device to detect moton."""
        res = await self._request("rules", fresh=True)
        return res["data"]  # type:ignore[no-any-return]

    async def set_rules(self, rules: list[MotionRule]) -> tuple[MotionRule, ...]:
        """Set motion rules."""
        json = {"rules": [rule.json() for rule in rules]}
        res = await self._request("rules", json=json, method=HTTPMethod.POST)
        return tuple(MotionRule(**i) for i in res["data"]["rules"])

    async def delete_rules(self) -> None:
        """Delete motion rules."""
        json = {"all": True}
        await self._request("rules", json=json, method=HTTPMethod.DELETE)

    async def get_activity_summary(
        self, device: SkybellDevice | None = None
    ) -> tuple[ActivitySummary, ...]:
        """Get activity summary."""
        params = {}
        if device:
            params["device"] = device.info.device_id
        if res := await self._request("activity/summary", params=params):
            self.activitySummary = tuple(ActivitySummary(**i) for i in res["data"])
        return self.activitySummary

    async def get_activity_details(self, activity_id: str) -> ActivityDetails:
        """Get more detailed information on an activity."""
        res = await self._request(f"activity/{activity_id}")
        return ActivityDetails(**res["data"])

    async def get_activity(
        self,
        offset: int | None = None,
        start: date | None = None,
        end: date | None = None,
        type: EventType = EventType.NONE,
        limit: int = 5,
        nopreviews: bool = False,
        device: SkybellDevice | None = None,
    ) -> tuple[Activity, ...]:
        """Get activity summary. A request for multiple days will not get image previews."""
        params = {"limit": limit, "nopreviews": str(nopreviews), "type": type.value}
        if offset:
            params["offset"] = offset
        if start:
            if not isinstance(start, datetime):
                start = datetime.combine(start, dt_time())
            params["start"] = int(start.timestamp())
        if end:
            if not isinstance(end, datetime):
                end = datetime.combine(end, dt_time())
            params["end"] = int(end.timestamp())
        if device:
            params["device"] = device.info.device_id
        if res := await self._request("activity", params=params):
            return tuple(Activity(**i) for i in res["data"]["rows"])
        return ()

    async def get_activity_video_url(
        self, activity: Activity | str | None = None
    ) -> str:
        """Get activity video. Return latest if no video specified."""
        if not activity and (act := self.latest_activity()):
            activity = act.activity_id
        elif isinstance(activity, Activity):
            activity = activity.activity_id
        res = await self._request(f"activity/{activity}/video")
        return res["data"]["download_url"]  # type:ignore[no-any-return]

    async def delete_activity(self, activity: Activity) -> None:
        """Download an activity."""
        await self._request(
            f"activity/{activity.activity_id}", method=HTTPMethod.DELETE
        )

    async def get_triggers(self) -> list:
        """Get triggers."""
        return (await self._request("triggers"))["data"]  # type:ignore[no-any-return]

    async def fetch_latest_activities(
        self, start: date | None = None, end: date | None = None, **kwargs: dict[str, Any]
    ) -> tuple[Activity, ...]:
        """Get activities with previews from given datetime range. Get all events if no range given."""
        end_dt = end if end else date.today()
        if start:
            start_dt = start
        else:
            start_dt = datetime.combine(end_dt - timedelta(days=30), dt_time())

        current = end_dt.date() if isinstance(end_dt, datetime) else end_dt
        start_dt = start_dt.date() if isinstance(start_dt, datetime) else start_dt
        activities: list[Activity] = []
        while current >= start_dt:
            if res := await self.get_activity(
                start=current, end=current + timedelta(days=1), **kwargs
            ):
                activities.extend(res)
            current -= timedelta(days=1)
        if not activities:
            return self.activities
        return tuple(activities)

    async def redeem_invite(self, invite: str) -> None:
        """Redeem an invite token."""
        await self._request(f"shares/{invite}/redeem")

    async def remove_share(self, share_id: str) -> None:
        """Remove another's access to a device."""
        await self._request(f"shares/{share_id}", method=HTTPMethod.DELETE)

    async def set_readonly_permission(self, share_id: str, read: bool) -> None:
        """Set share permission with given id. Set read as False to give write permission."""
        json = {"readOnly": read}
        await self._request(f"shares/{share_id}", json=json, method=HTTPMethod.PUT)

    async def add_device(self) -> dict[str, Any]:
        """Add a device. This is currently only meant to be done with the mobile app."""
        res = await self._request("devices/provision")
        return res["data"]  # type:ignore[no-any-return]

    def latest_activity(
        self, type: str | EventType | None = None, device: SkybellDevice | None = None
    ) -> Activity | None:
        """Get the latest activity for the specified type. Use get_activity for newer activities."""
        return latest(self.activities, type, device)

    async def get_tones(self) -> tuple[Tone, ...]:
        """Get available tones."""
        res = await self._request("tones")
        return tuple(Tone(**i) for i in res["data"])

    async def download_tone(self, tone: Tone) -> bytes:
        """Download the given tone."""
        res = await self._session.get(
            f"https://dlc.skybell.network/tones/doorbell/{tone.file}",
            raise_for_status=True,
        )
        return await res.read()

    @property
    def activities(self) -> tuple[Activity, ...]:
        """Return the activities from all devices."""
        return tuple(activity for d in self.devices for activity in d.activities)

    @property
    def activities_dict(self) -> dict[str, Activity]:
        """Return the activities from all devices with the event ids as keys."""
        return {a.activity_id: a for d in self.devices for a in d.activities}

    @cached_property
    def all_tones(self) -> dict[str, str]:
        """Return all tones including the default not valid for on demand play."""
        return self.tones | {"Default tone": "Default tone"}

    @cached_property
    def tone_file_dict(self) -> dict[str, str]:
        """Return dictionary of tones names with the file names as keys."""
        return {v: k for k, v in self.all_tones.items()}

    @property
    def user(self) -> User:
        """Return information in the signed in user."""
        if self._user:
            return self._user
        raise AttributeError("initialize must be called first.")

    @property
    def auth(self) -> Auth:
        """Return authorization information."""
        if self._auth:
            return self._auth
        raise AttributeError("initialize must be called first.")

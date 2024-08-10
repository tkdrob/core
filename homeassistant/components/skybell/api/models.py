"""Pydantic models for AIOSkybell."""

from __future__ import annotations

import base64
from datetime import UTC, date, datetime
from ipaddress import IPv4Address, IPv4Network
from logging import DEBUG
import struct
from typing import TYPE_CHECKING, Any, NotRequired, TypedDict

import ciso8601
from orjson import dumps as orjson_dumps, loads

try:
    from pydantic import (  # pylint:disable=no-name-in-module
        BaseModel,
        error_wrappers,
        root_validator,
        validate_model,
        validator,
    )
except ImportError:
    # pylint:disable-next=no-name-in-module
    from pydantic.v1 import (  # type:ignore[no-redef]
        BaseModel,
        error_wrappers,
        root_validator,
        validate_model,
        validator,
    )

from .const import LOGGER, REPO_URL, EventType, ImageQuality, LiveVolume, Volume

if TYPE_CHECKING:
    from .device import SkybellDevice

DT_CONVERTIBLES = (
    "boot_time",
    "created_at",
    "date_time",
    "eula_accepted",
    "event_time",
    "invite_sent",
    "last_connected",
    "last_disconnected",
    "last_update",
    "modified",
    "ready_time",
    "updated_at",
    "user_since",
    "video_ready_time",
)


def dumps(obj: dict[str, Any], *, default: Any = None) -> str:
    """Dump with orjson."""
    return orjson_dumps(obj, default=default).decode()


object_setattr = object.__setattr__

EXTRA = "ignore" if LOGGER.getEffectiveLevel() > DEBUG else "forbid"


class Base(BaseModel):
    """Frozen Base Model class to allow extra attributes for pydantic."""

    class Config:
        """Pydantic config."""

        extra = EXTRA  # type:ignore[pydantic-config]
        frozen = True
        json_dumps = dumps
        json_loads = loads

    def __init__(self, **data: Any) -> None:
        """Initialize. Warn of extra attributes are given by the API to be reported."""
        values, fields_set, validation_error = validate_model(self.__class__, data)
        if validation_error:
            LOGGER.warning(
                "%s.\ndata: %s\nPlease report this: %s",
                validation_error,
                data,
                REPO_URL,
            )
        try:
            object_setattr(self, "__dict__", values)
        except TypeError as e:
            raise TypeError(
                "Model values must be a dict; you may not have returned a dictionary from a root validator"
            ) from e
        object_setattr(self, "__fields_set__", fields_set)
        self._init_private_attributes()

    @validator(
        *DT_CONVERTIBLES,
        pre=True,
        check_fields=False,
    )
    def _parse_dt(cls, value: str | int | datetime) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, int):
            if len(str(value)) == 13:
                value //= 1000
            return datetime.fromtimestamp(value, tz=UTC)
        return ciso8601.parse_datetime(value).replace(tzinfo=UTC)

    @validator("date", pre=True, check_fields=False)
    def _parse_date(cls, value: str) -> date:
        return datetime.strptime(value, "%m/%d/%Y").date()

    @validator("image", "preview", pre=True, check_fields=False)
    def _parse_image(cls, value: str | dict) -> bytes:
        if isinstance(value, str):
            return base64.b64decode(value)
        return struct.pack(f'{len(value["data"])}I', *value["data"])

    @validator(
        "led_color",
        "outdoor_chime_color",
        "motion_chime_color",
        pre=True,
        check_fields=False,
    )
    def _parse_color(cls, value: str | tuple) -> tuple[int, int, int]:
        if not value:
            return 0, 0, 0
        if isinstance(value, tuple):
            return value
        r, g, b = (int(value.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
        return r, g, b

    @validator("MAC_address", pre=True, check_fields=False)
    def _format_mac(cls, value: str) -> str:
        return value.lower()


class Auth(Base):
    """Authentication info."""

    AccessToken: str
    email: str | None = None
    ExpiresAt: float
    ExpiresIn: int
    IdToken: str
    password: str | None = None
    RefreshToken: str
    TokenType: str


class User(Base):
    """User details."""

    account_id: str
    email: str
    eula_accepted: datetime
    fname: str
    hd_user_id: str  # old user id
    lname: str
    premium: None
    rsos_eula_accepted: bool
    user_since: datetime


class MotionZone(Base):
    """Motion zone."""

    ignore: bool
    sensitivity: int


class MotionZoneConfig(Base):
    """Motion zone configuration. 4 set of 3 MotionZone objects. Start left to right, top down on the camera image."""

    x: int
    y: int
    zones: list[list[MotionZone]]


class BasicMotion(Base, frozen=False):
    """Base motion settings."""

    fd_notify: bool = False
    fd_record: bool = False
    hbd_notify: bool = False
    hbd_record: bool = False
    motion_notify: bool = False
    motion_record: bool = False


class Settings(Base):
    """Settings details."""

    account_id: str
    audio_alarm_enabled: bool = False
    audio_cmd_enabled: bool = False
    aws_region: str | None = None
    basic_motion: BasicMotion | None = None
    brightness: int
    button_pressed: bool = False
    chime_file_motion: str
    chime_file: str
    debug_motion_detect: bool = False
    device_id: str
    device_lat: float | None = None
    device_lon: float | None = None
    device_name: str
    digital_chime: bool = False
    event_duration: int = 0
    fd_sensitivity: int = 0
    force_turn: bool = False
    fr_sensitivity: int = 0
    hmbd_sensitivity: int = 0
    image_quality: ImageQuality | None = None
    indoor_chime: bool = False
    led_color_brightness: int = 0
    led_color: tuple[int, int, int]
    motion_chime_color: tuple[int, int, int]
    motion_chime_volume: Volume  # TODO
    motion_chime: bool
    motion_detection: bool = False
    motion_sensitivity: int = 0
    motion_zone_config: MotionZoneConfig | None = None
    outdoor_chime_color: tuple[int, int, int]
    outdoor_chime_volume: Volume  # TODO
    outdoor_chime: bool
    pir_sensitivity: int = 0
    speaker_volume: LiveVolume | None = None
    telemetry_freq: int
    time_zone: str
    using_rules: bool = False
    video_datetime: bool = False
    video_rotation: int = 0

    @root_validator(pre=True)
    def _volume(cls, values: dict[str, Any]) -> dict[str, Any]:
        for setting in ("motion_chime", "outdoor_chime"):
            if values.get(setting):
                continue
            values[f"{setting}_volume"] = Volume.off
        return values


class ChangeableSettings(BaseModel):
    """Changeable settings details."""

    audio_alarm_enabled: bool | None = None
    audio_cmd_enabled: bool | None = None
    basic_motion: BasicMotion | None = None
    button_pressed: bool | None = None
    chime_file_motion: str | None = None
    chime_file: str | None = None
    debug_motion_detect: bool | None = None
    device_name: str | None = None
    digital_chime: bool | None = None
    event_duration: int | None = None
    fd_sensitivity: int | None = None
    force_turn: bool | None = None
    fr_sensitivity: int | None = None
    hmbd_sensitivity: int | None = None
    image_quality: ImageQuality | None = None
    indoor_chime: bool | None = None
    led_color_brightness: int | None = None
    led_color: str | tuple[int, int, int] | None = None
    motion_chime_color_brightness: int | None = None
    motion_chime_color: str | tuple[int, int, int] | None = None
    motion_chime_volume: Volume | None = None
    motion_chime: bool | None = None
    motion_detection: bool | None = None
    motion_sensitivity: int | None = None
    motion_zone_config: MotionZoneConfig | None = None
    outdoor_chime_color_brightness: int | None = None
    outdoor_chime_color: str | tuple[int, int, int] | None = None
    outdoor_chime_volume: Volume | None = None
    outdoor_chime: bool | None = None
    pir_sensitivity: int | None = None
    speaker_volume: Volume | None = None
    telemetry_freq: int | None = None
    time_zone: str | None = None
    using_rules: bool | None = None
    video_datetime: bool | None = None
    video_rotation: int | None = None

    @root_validator(pre=True)
    def _volume(cls, values: dict[str, Any]) -> dict[str, Any]:
        for setting in ("motion_chime", "outdoor_chime"):
            vol = f"{setting}_volume"
            if not (volume := values.get(vol)):
                continue
            if volume == Volume.off:
                values.pop(vol)
                values[setting] = False
            else:
                values[setting] = True
        return values

    @root_validator(pre=True)
    def _color(cls, values: dict[str, Any]) -> dict[str, Any]:
        for attr in (
            "led_color_brightness",
            "outdoor_chime_color_brightness",
            "motion_chime_color_brightness",
        ):
            if brightness := values.pop(attr, None):
                color_setting = attr[:-11]
                if color := values.get(color_setting):
                    color = tuple(round(c * brightness / max(color)) for c in color)
                    values[color_setting] = color
                else:  # pylint:disable-next=c-extension-no-member
                    raise error_wrappers.ValidationError(
                        [f"{color_setting} is required when giving {attr}"], type(cls)
                    )
        return values

    @validator(
        "led_color",
        "outdoor_chime_color",
        "motion_chime_color",
        pre=True,
        check_fields=False,
    )
    def _parse_color(cls, value: tuple[int, int, int]) -> str:
        return "#{:02X}{:02X}{:02X}".format(*value)


class DeviceSettings(Base):
    """Device settings."""

    ESSID: str | None = None
    firmware_major_release: int
    firmware_minor_release: int
    firmware_patch: int
    firmware_version: str
    hardware_version: str
    MAC_address: str
    model_rev: str
    OTA_signature: None = None
    OTA_type: None = None
    OTA_version: None = None
    serial_number: str


class ToneSetting(Base):
    """Tone setting details."""

    file: str = "Default tone"
    last_updated: datetime = datetime.now(tz=UTC)


class Tones(Base):
    """Tone settings."""

    button: ToneSetting
    motion: ToneSetting
    test: None

    @validator("button", "motion", pre=True)
    def _default_tone(
        cls, value: dict[str, Any] | None
    ) -> dict[str, Any] | ToneSetting:
        return value or ToneSetting()


class DeviceTelemetry(Base):
    """Device telemetry details."""

    boot_time: datetime | None = None
    gateway: IPv4Address | None = None
    ip_address_public: IPv4Address | None = None
    ip_address: IPv4Address | None = None
    ip_subnet: IPv4Network | None = None
    last_seen: datetime | None = None
    link_quality: str | None = None  # 49/70
    network_frequency: float | None = None
    signal_level: int  # dB
    timestamp: datetime | None = None
    upload_stats: str | None = None
    uptime: int | None = None
    wifi_bit_rate: str | None = None
    wifi_noise: str | None = None


class DeviceInfo(Base, frozen=False):
    """Device details from /devices/{device_id} endpoint."""

    account_id: str
    basic_motion: BasicMotion
    certificate_id: str
    client_id: str
    created_at: datetime
    device_id: str
    device_settings: DeviceSettings
    doorlock_id: None
    firmware: str
    hardware: str
    invite_token: str
    last_connected: datetime
    last_disconnected: datetime | None
    last_event: int | None
    lat: float | None
    lon: float | None
    manufactured: None
    name: str
    rapidsos: None
    serial: str
    settings: Settings
    share_id: str | None = None
    shared_read_only: bool = False
    shared: bool = False
    tones: Tones
    updated_at: datetime
    telemetry: DeviceTelemetry | None = None
    using_rules: bool


class Snapshot(Base):
    """A snapshot."""

    date_time: datetime
    preview: bytes


class MotionRuleActions(Base):
    """Motion rule actions."""

    animation_duration: None
    animation: None
    audio_notify_message: None
    audio_notify: None
    chime_type: None
    chime: None
    light_on_duration: None
    light_on_level: None
    light_on: None
    notify_tags: None
    notify: None
    pre_roll_duration: int
    pre_roll: bool
    record_duration: None
    record: None
    snapshot: None
    sound_type: None
    sound: None


class MotionRuleTrigger(Base):
    """Motion rule trigger."""

    count: int
    event: str


class MotionRule(Base):
    """Motion rule settings."""

    actions: MotionRuleActions
    internal: bool
    light_levels: None
    match_count: int
    rule_num: int
    temperature_levels: None
    triggers: list[MotionRuleTrigger]
    window: int


class MotionSettings(Base):
    """Motion settings."""

    basic_motion: BasicMotion
    motion_detection: bool
    motion_sensitivity: int
    pir_sensitivity: int
    using_rules: bool


class Tone(Base):
    """Tone available for playback."""

    classicDingDong: bool
    file: str
    modified: datetime
    name: str
    size: int
    url: str


class ActivitySummary(Base):
    """Summary of available activities."""

    activity_day: date
    event_count: int


class AIPPE(Base):
    """Artificial intelligence detected persons."""

    PersonsIndeterminate: tuple[int, ...]
    PersonsWithRequiredEquipment: tuple[int, ...]
    PersonsWithoutRequiredEquipment: tuple[int, ...]


class Activity(Base):
    """Information on an activity."""

    account_id: str
    activity_id: str
    ai_ppe: AIPPE | None
    created_at: datetime
    date: date
    device_id: str
    device_name: str
    edge_tags: list[str] | None
    event_time: datetime
    event_type: EventType
    events: tuple[str, ...]
    image: bytes | None
    video_ready_time: datetime | None = None
    video_ready: bool
    video_size: int | None = None
    video_url: str


class ActivityMetadata(Base):
    """Metadata for an activity."""

    key: str | None = None
    ready_time: datetime | None = None
    size: int | None = None
    video_length: int | None = None


class ActivityEvent(Base):
    """Event for an activity."""

    edge_tags: tuple[str, ...] = ()
    event_type: EventType
    imageHash: str
    timestamp: datetime


class ActivityDetails(Base):
    """More detailed information on an activity."""

    account_id: str
    activity_id: str
    ai_ppe: None
    client_id: str
    created_at: datetime
    date: date
    device_id: str
    device_name: str
    edge_tags: list[str] | None
    event_time: datetime | None
    event_type: EventType
    events: tuple[ActivityEvent, ...]
    faces: None
    has_video: bool
    image: bytes | None
    metadata: ActivityMetadata
    premium_status: str  # free
    updated_at: datetime
    video_ready: bool


class SharedDeviceSettings(Base):
    """Class for shared device settings."""

    button_pressed: bool = False
    motion_detection: bool


class Share(Base):
    """Class for a device share."""

    accepted: bool
    client_id: str
    created_at: datetime
    device_name: str
    invite_sent: datetime
    invite_token: str
    invited_email: str
    readOnly: bool
    share_id: str
    shared_device_id: str
    shared_to_account_id: str
    shared_user_device_settings: SharedDeviceSettings
    sharing_account_id: str
    updated_at: datetime


class ActivityOptions(TypedDict):
    """Typed dictionary for activity queries."""

    device: NotRequired[SkybellDevice]
    end: NotRequired[date]
    limit: NotRequired[int]
    nopreviews: NotRequired[bool]
    offset: NotRequired[int]
    start: NotRequired[date]
    type: NotRequired[EventType]

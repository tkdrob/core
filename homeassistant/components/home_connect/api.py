"""API for Home Connect bound to HASS OAuth."""

from asyncio import run_coroutine_threadsafe
import logging

import homeconnect
from homeconnect.api import HomeConnectError

from homeassistant import config_entries, core
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_ICON,
    ATTR_NAME,
    CONF_DEVICE,
    CONF_ENTITIES,
    DEVICE_CLASS_TIMESTAMP,
    PERCENTAGE,
    TIME_SECONDS,
)
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.dispatcher import dispatcher_send

from .const import (
    ATTR_AMBIENT,
    ATTR_DESC,
    ATTR_DEVICE,
    ATTR_KEY,
    ATTR_SENSOR_TYPE,
    ATTR_SIGN,
    ATTR_UNIT,
    ATTR_VALUE,
    BSH_ACTIVE_PROGRAM,
    BSH_OPERATION_STATE,
    BSH_POWER_OFF,
    BSH_POWER_STANDBY,
    SIGNAL_UPDATE_ENTITIES,
)

_LOGGER = logging.getLogger(__name__)


class ConfigEntryAuth(homeconnect.HomeConnectAPI):
    """Provide Home Connect authentication tied to an OAuth2 based config entry."""

    def __init__(
        self,
        hass: core.HomeAssistant,
        config_entry: config_entries.ConfigEntry,
        implementation: config_entry_oauth2_flow.AbstractOAuth2Implementation,
    ):
        """Initialize Home Connect Auth."""
        self.hass = hass
        self.config_entry = config_entry
        self.session = config_entry_oauth2_flow.OAuth2Session(
            hass, config_entry, implementation
        )
        super().__init__(self.session.token)
        self.devices = []

    def refresh_tokens(self) -> dict:
        """Refresh and return new Home Connect tokens using Home Assistant OAuth2 session."""
        run_coroutine_threadsafe(
            self.session.async_ensure_token_valid(), self.hass.loop
        ).result()

        return self.session.token

    def get_devices(self):
        """Get a dictionary of devices."""
        appl = self.get_appliances()
        devices = []
        for app in appl:
            if app.type == "Dryer":
                device = Dryer(self.hass, app)
            elif app.type == "Washer":
                device = Washer(self.hass, app)
            elif app.type == "Dishwasher":
                device = Dishwasher(self.hass, app)
            elif app.type == "FridgeFreezer":
                device = FridgeFreezer(self.hass, app)
            elif app.type == "Oven":
                device = Oven(self.hass, app)
            elif app.type == "CoffeeMaker":
                device = CoffeeMaker(self.hass, app)
            elif app.type == "Hood":
                device = Hood(self.hass, app)
            elif app.type == "Hob":
                device = Hob(self.hass, app)
            else:
                _LOGGER.warning("Appliance type %s not implemented", app.type)
                continue
            devices.append(
                {CONF_DEVICE: device, CONF_ENTITIES: device.get_entity_info()}
            )
        self.devices = devices
        return devices


class HomeConnectDevice:
    """Generic Home Connect device."""

    # for some devices, this is instead BSH_POWER_STANDBY
    # see https://developer.home-connect.com/docs/settings/power_state
    power_off_state = BSH_POWER_OFF

    def __init__(self, hass, appliance):
        """Initialize the device class."""
        self.hass = hass
        self.appliance = appliance

    def initialize(self):
        """Fetch the info needed to initialize the device."""
        try:
            self.appliance.get_status()
        except (HomeConnectError, ValueError):
            _LOGGER.debug("Unable to fetch appliance status. Probably offline")
        try:
            self.appliance.get_settings()
        except (HomeConnectError, ValueError):
            _LOGGER.debug("Unable to fetch settings. Probably offline")
        try:
            program_active = self.appliance.get_programs_active()
        except (HomeConnectError, ValueError):
            _LOGGER.debug("Unable to fetch active programs. Probably offline")
            program_active = None
        if program_active and ATTR_KEY in program_active:
            self.appliance.status[BSH_ACTIVE_PROGRAM] = {
                ATTR_VALUE: program_active[ATTR_KEY]
            }
        self.appliance.listen_events(callback=self.event_callback)

    def event_callback(self, appliance):
        """Handle event."""
        _LOGGER.debug("Update triggered on %s", appliance.name)
        _LOGGER.debug(self.appliance.status)
        dispatcher_send(self.hass, SIGNAL_UPDATE_ENTITIES, appliance.haId)


class DeviceWithPrograms(HomeConnectDevice):
    """Device with programs."""

    PROGRAMS = []

    def get_programs_available(self):
        """Get the available programs."""
        return self.PROGRAMS

    def get_program_switches(self):
        """Get a dictionary with info about program switches.

        There will be one switch for each program.
        """
        programs = self.get_programs_available()
        return [{ATTR_DEVICE: self, "program_name": p["name"]} for p in programs]

    def get_program_sensors(self):
        """Get a dictionary with info about program sensors.

        There will be one of the four types of sensors for each
        device.
        """
        sensors = {
            "Remaining Program Time": (None, None, DEVICE_CLASS_TIMESTAMP, 1),
            "Duration": (TIME_SECONDS, "mdi:update", None, 1),
            "Program Progress": (PERCENTAGE, "mdi:progress-clock", None, 1),
        }
        return [
            {
                ATTR_DEVICE: self,
                ATTR_DESC: k,
                ATTR_UNIT: unit,
                ATTR_KEY: "BSH.Common.Option.{}".format(k.replace(" ", "")),
                ATTR_ICON: icon,
                ATTR_DEVICE_CLASS: device_class,
                ATTR_SIGN: sign,
            }
            for k, (unit, icon, device_class, sign) in sensors.items()
        ]


class DeviceWithOpState(HomeConnectDevice):
    """Device that has an operation state sensor."""

    def get_opstate_sensor(self):
        """Get a list with info about operation state sensors."""

        return [
            {
                ATTR_DEVICE: self,
                ATTR_DESC: "Operation State",
                ATTR_UNIT: None,
                ATTR_KEY: BSH_OPERATION_STATE,
                ATTR_ICON: "mdi:state-machine",
                ATTR_DEVICE_CLASS: None,
                ATTR_SIGN: 1,
            }
        ]


class DeviceWithDoor(HomeConnectDevice):
    """Device that has a door sensor."""

    def get_door_entity(self):
        """Get a dictionary with info about the door binary sensor."""
        return {
            ATTR_DEVICE: self,
            ATTR_DESC: "Door",
            ATTR_SENSOR_TYPE: "door",
            ATTR_DEVICE_CLASS: "door",
        }


class DeviceWithLight(HomeConnectDevice):
    """Device that has lighting."""

    def get_light_entity(self):
        """Get a dictionary with info about the lighting."""
        return {ATTR_DEVICE: self, ATTR_DESC: "Light", ATTR_AMBIENT: None}


class DeviceWithAmbientLight(HomeConnectDevice):
    """Device that has ambient lighting."""

    def get_ambientlight_entity(self):
        """Get a dictionary with info about the ambient lighting."""
        return {ATTR_DEVICE: self, ATTR_DESC: "AmbientLight", ATTR_AMBIENT: True}


class DeviceWithRemoteControl(HomeConnectDevice):
    """Device that has Remote Control binary sensor."""

    def get_remote_control(self):
        """Get a dictionary with info about the remote control sensor."""
        return {
            ATTR_DEVICE: self,
            ATTR_DESC: "Remote Control",
            ATTR_SENSOR_TYPE: "remote_control",
        }


class DeviceWithRemoteStart(HomeConnectDevice):
    """Device that has a Remote Start binary sensor."""

    def get_remote_start(self):
        """Get a dictionary with info about the remote start sensor."""
        return {
            ATTR_DEVICE: self,
            ATTR_DESC: "Remote Start",
            ATTR_SENSOR_TYPE: "remote_start",
        }


class Dryer(
    DeviceWithDoor,
    DeviceWithOpState,
    DeviceWithPrograms,
    DeviceWithRemoteControl,
    DeviceWithRemoteStart,
):
    """Dryer class."""

    PROGRAMS = [
        {ATTR_NAME: "LaundryCare.Dryer.Program.Cotton"},
        {ATTR_NAME: "LaundryCare.Dryer.Program.Synthetic"},
        {ATTR_NAME: "LaundryCare.Dryer.Program.Mix"},
        {ATTR_NAME: "LaundryCare.Dryer.Program.Blankets"},
        {ATTR_NAME: "LaundryCare.Dryer.Program.BusinessShirts"},
        {ATTR_NAME: "LaundryCare.Dryer.Program.DownFeathers"},
        {ATTR_NAME: "LaundryCare.Dryer.Program.Hygiene"},
        {ATTR_NAME: "LaundryCare.Dryer.Program.Jeans"},
        {ATTR_NAME: "LaundryCare.Dryer.Program.Outdoor"},
        {ATTR_NAME: "LaundryCare.Dryer.Program.SyntheticRefresh"},
        {ATTR_NAME: "LaundryCare.Dryer.Program.Towels"},
        {ATTR_NAME: "LaundryCare.Dryer.Program.Delicates"},
        {ATTR_NAME: "LaundryCare.Dryer.Program.Super40"},
        {ATTR_NAME: "LaundryCare.Dryer.Program.Shirts15"},
        {ATTR_NAME: "LaundryCare.Dryer.Program.Pillow"},
        {ATTR_NAME: "LaundryCare.Dryer.Program.AntiShrink"},
    ]

    def get_entity_info(self):
        """Get a dictionary with infos about the associated entities."""
        door_entity = self.get_door_entity()
        remote_control = self.get_remote_control()
        remote_start = self.get_remote_start()
        op_state_sensor = self.get_opstate_sensor()
        program_sensors = self.get_program_sensors()
        program_switches = self.get_program_switches()
        return {
            "binary_sensor": [door_entity, remote_control, remote_start],
            "switch": program_switches,
            "sensor": program_sensors + op_state_sensor,
        }


class Dishwasher(
    DeviceWithDoor,
    DeviceWithAmbientLight,
    DeviceWithOpState,
    DeviceWithPrograms,
    DeviceWithRemoteControl,
    DeviceWithRemoteStart,
):
    """Dishwasher class."""

    PROGRAMS = [
        {ATTR_NAME: "Dishcare.Dishwasher.Program.Auto1"},
        {ATTR_NAME: "Dishcare.Dishwasher.Program.Auto2"},
        {ATTR_NAME: "Dishcare.Dishwasher.Program.Auto3"},
        {ATTR_NAME: "Dishcare.Dishwasher.Program.Eco50"},
        {ATTR_NAME: "Dishcare.Dishwasher.Program.Quick45"},
        {ATTR_NAME: "Dishcare.Dishwasher.Program.Intensiv70"},
        {ATTR_NAME: "Dishcare.Dishwasher.Program.Normal65"},
        {ATTR_NAME: "Dishcare.Dishwasher.Program.Glas40"},
        {ATTR_NAME: "Dishcare.Dishwasher.Program.GlassCare"},
        {ATTR_NAME: "Dishcare.Dishwasher.Program.NightWash"},
        {ATTR_NAME: "Dishcare.Dishwasher.Program.Quick65"},
        {ATTR_NAME: "Dishcare.Dishwasher.Program.Normal45"},
        {ATTR_NAME: "Dishcare.Dishwasher.Program.Intensiv45"},
        {ATTR_NAME: "Dishcare.Dishwasher.Program.AutoHalfLoad"},
        {ATTR_NAME: "Dishcare.Dishwasher.Program.IntensivPower"},
        {ATTR_NAME: "Dishcare.Dishwasher.Program.MagicDaily"},
        {ATTR_NAME: "Dishcare.Dishwasher.Program.Super60"},
        {ATTR_NAME: "Dishcare.Dishwasher.Program.Kurz60"},
        {ATTR_NAME: "Dishcare.Dishwasher.Program.ExpressSparkle65"},
        {ATTR_NAME: "Dishcare.Dishwasher.Program.MachineCare"},
        {ATTR_NAME: "Dishcare.Dishwasher.Program.SteamFresh"},
        {ATTR_NAME: "Dishcare.Dishwasher.Program.MaximumCleaning"},
    ]

    def get_entity_info(self):
        """Get a dictionary with infos about the associated entities."""
        door_entity = self.get_door_entity()
        remote_control = self.get_remote_control()
        remote_start = self.get_remote_start()
        op_state_sensor = self.get_opstate_sensor()
        program_sensors = self.get_program_sensors()
        program_switches = self.get_program_switches()
        return {
            "binary_sensor": [door_entity, remote_control, remote_start],
            "switch": program_switches,
            "sensor": program_sensors + op_state_sensor,
        }


class Oven(
    DeviceWithDoor,
    DeviceWithOpState,
    DeviceWithPrograms,
    DeviceWithRemoteControl,
    DeviceWithRemoteStart,
):
    """Oven class."""

    PROGRAMS = [
        {ATTR_NAME: "Cooking.Oven.Program.HeatingMode.PreHeating"},
        {ATTR_NAME: "Cooking.Oven.Program.HeatingMode.HotAir"},
        {ATTR_NAME: "Cooking.Oven.Program.HeatingMode.TopBottomHeating"},
        {ATTR_NAME: "Cooking.Oven.Program.HeatingMode.PizzaSetting"},
        {ATTR_NAME: "Cooking.Oven.Program.Microwave.600Watt"},
    ]

    power_off_state = BSH_POWER_STANDBY

    def get_entity_info(self):
        """Get a dictionary with infos about the associated entities."""
        door_entity = self.get_door_entity()
        remote_control = self.get_remote_control()
        remote_start = self.get_remote_start()
        op_state_sensor = self.get_opstate_sensor()
        program_sensors = self.get_program_sensors()
        program_switches = self.get_program_switches()
        return {
            "binary_sensor": [door_entity, remote_control, remote_start],
            "switch": program_switches,
            "sensor": program_sensors + op_state_sensor,
        }


class Washer(
    DeviceWithDoor,
    DeviceWithOpState,
    DeviceWithPrograms,
    DeviceWithRemoteControl,
    DeviceWithRemoteStart,
):
    """Washer class."""

    PROGRAMS = [
        {ATTR_NAME: "LaundryCare.Washer.Program.Cotton"},
        {ATTR_NAME: "LaundryCare.Washer.Program.Cotton.CottonEco"},
        {ATTR_NAME: "LaundryCare.Washer.Program.EasyCare"},
        {ATTR_NAME: "LaundryCare.Washer.Program.Mix"},
        {ATTR_NAME: "LaundryCare.Washer.Program.DelicatesSilk"},
        {ATTR_NAME: "LaundryCare.Washer.Program.Wool"},
        {ATTR_NAME: "LaundryCare.Washer.Program.Sensitive"},
        {ATTR_NAME: "LaundryCare.Washer.Program.Auto30"},
        {ATTR_NAME: "LaundryCare.Washer.Program.Auto40"},
        {ATTR_NAME: "LaundryCare.Washer.Program.Auto60"},
        {ATTR_NAME: "LaundryCare.Washer.Program.Chiffon"},
        {ATTR_NAME: "LaundryCare.Washer.Program.Curtains"},
        {ATTR_NAME: "LaundryCare.Washer.Program.DarkWash"},
        {ATTR_NAME: "LaundryCare.Washer.Program.Dessous"},
        {ATTR_NAME: "LaundryCare.Washer.Program.Monsoon"},
        {ATTR_NAME: "LaundryCare.Washer.Program.Outdoor"},
        {ATTR_NAME: "LaundryCare.Washer.Program.PlushToy"},
        {ATTR_NAME: "LaundryCare.Washer.Program.ShirtsBlouses"},
        {ATTR_NAME: "LaundryCare.Washer.Program.SportFitness"},
        {ATTR_NAME: "LaundryCare.Washer.Program.Towels"},
        {ATTR_NAME: "LaundryCare.Washer.Program.WaterProof"},
    ]

    def get_entity_info(self):
        """Get a dictionary with infos about the associated entities."""
        door_entity = self.get_door_entity()
        remote_control = self.get_remote_control()
        remote_start = self.get_remote_start()
        op_state_sensor = self.get_opstate_sensor()
        program_sensors = self.get_program_sensors()
        program_switches = self.get_program_switches()
        return {
            "binary_sensor": [door_entity, remote_control, remote_start],
            "switch": program_switches,
            "sensor": program_sensors + op_state_sensor,
        }


class CoffeeMaker(DeviceWithOpState, DeviceWithPrograms, DeviceWithRemoteStart):
    """Coffee maker class."""

    PROGRAMS = [
        {ATTR_NAME: "ConsumerProducts.CoffeeMaker.Program.Beverage.Espresso"},
        {ATTR_NAME: "ConsumerProducts.CoffeeMaker.Program.Beverage.EspressoMacchiato"},
        {ATTR_NAME: "ConsumerProducts.CoffeeMaker.Program.Beverage.Coffee"},
        {ATTR_NAME: "ConsumerProducts.CoffeeMaker.Program.Beverage.Cappuccino"},
        {ATTR_NAME: "ConsumerProducts.CoffeeMaker.Program.Beverage.LatteMacchiato"},
        {ATTR_NAME: "ConsumerProducts.CoffeeMaker.Program.Beverage.CaffeLatte"},
        {ATTR_NAME: "ConsumerProducts.CoffeeMaker.Program.CoffeeWorld.Americano"},
        {ATTR_NAME: "ConsumerProducts.CoffeeMaker.Program.Beverage.EspressoDoppio"},
        {ATTR_NAME: "ConsumerProducts.CoffeeMaker.Program.CoffeeWorld.FlatWhite"},
        {ATTR_NAME: "ConsumerProducts.CoffeeMaker.Program.CoffeeWorld.Galao"},
        {ATTR_NAME: "ConsumerProducts.CoffeeMaker.Program.Beverage.MilkFroth"},
        {ATTR_NAME: "ConsumerProducts.CoffeeMaker.Program.Beverage.WarmMilk"},
        {ATTR_NAME: "ConsumerProducts.CoffeeMaker.Program.Beverage.Ristretto"},
        {ATTR_NAME: "ConsumerProducts.CoffeeMaker.Program.CoffeeWorld.Cortado"},
    ]

    power_off_state = BSH_POWER_STANDBY

    def get_entity_info(self):
        """Get a dictionary with infos about the associated entities."""
        remote_start = self.get_remote_start()
        op_state_sensor = self.get_opstate_sensor()
        program_sensors = self.get_program_sensors()
        program_switches = self.get_program_switches()
        return {
            "binary_sensor": [remote_start],
            "switch": program_switches,
            "sensor": program_sensors + op_state_sensor,
        }


class Hood(
    DeviceWithLight,
    DeviceWithAmbientLight,
    DeviceWithOpState,
    DeviceWithPrograms,
    DeviceWithRemoteControl,
    DeviceWithRemoteStart,
):
    """Hood class."""

    PROGRAMS = [
        {ATTR_NAME: "Cooking.Common.Program.Hood.Automatic"},
        {ATTR_NAME: "Cooking.Common.Program.Hood.Venting"},
        {ATTR_NAME: "Cooking.Common.Program.Hood.DelayedShutOff"},
    ]

    def get_entity_info(self):
        """Get a dictionary with infos about the associated entities."""
        remote_control = self.get_remote_control()
        remote_start = self.get_remote_start()
        light_entity = self.get_light_entity()
        ambientlight_entity = self.get_ambientlight_entity()
        op_state_sensor = self.get_opstate_sensor()
        program_sensors = self.get_program_sensors()
        program_switches = self.get_program_switches()
        return {
            "binary_sensor": [remote_control, remote_start],
            "switch": program_switches,
            "sensor": program_sensors + op_state_sensor,
            "light": [light_entity, ambientlight_entity],
        }


class FridgeFreezer(DeviceWithDoor):
    """Fridge/Freezer class."""

    def get_entity_info(self):
        """Get a dictionary with infos about the associated entities."""
        door_entity = self.get_door_entity()
        return {"binary_sensor": [door_entity]}


class Hob(DeviceWithOpState, DeviceWithPrograms, DeviceWithRemoteControl):
    """Hob class."""

    PROGRAMS = [{ATTR_NAME: "Cooking.Hob.Program.PowerLevelMode"}]

    def get_entity_info(self):
        """Get a dictionary with infos about the associated entities."""
        remote_control = self.get_remote_control()
        op_state_sensor = self.get_opstate_sensor()
        program_sensors = self.get_program_sensors()
        program_switches = self.get_program_switches()
        return {
            "binary_sensor": [remote_control],
            "switch": program_switches,
            "sensor": program_sensors + op_state_sensor,
        }

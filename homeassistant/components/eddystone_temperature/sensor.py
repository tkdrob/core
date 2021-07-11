"""
Read temperature information from Eddystone beacons.

Your beacons must be configured to transmit UID (for identification) and TLM
(for temperature) frames.
"""
import logging

# pylint: disable=import-error
from beacontools import BeaconScanner, EddystoneFilter, EddystoneTLMFrame
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.const import (
    CONF_NAME,
    EVENT_HOMEASSISTANT_START,
    EVENT_HOMEASSISTANT_STOP,
    STATE_UNKNOWN,
    TEMP_CELSIUS,
)
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

CONF_BEACONS = "beacons"
CONF_BT_DEVICE_ID = "bt_device_id"
CONF_INSTANCE = "instance"
CONF_NAMESPACE = "namespace"

BEACON_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAMESPACE): cv.string,
        vol.Required(CONF_INSTANCE): cv.string,
        vol.Optional(CONF_NAME): cv.string,
    }
)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_BT_DEVICE_ID, default=0): cv.positive_int,
        vol.Required(CONF_BEACONS): vol.Schema({cv.string: BEACON_SCHEMA}),
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Validate configuration, create devices and start monitoring thread."""
    bt_device_id = config.get("bt_device_id")

    beacons = config.get(CONF_BEACONS)
    devices = []

    for dev_name, properties in beacons.items():
        namespace = get_from_conf(properties, CONF_NAMESPACE, 20)
        instance = get_from_conf(properties, CONF_INSTANCE, 12)
        name = properties.get(CONF_NAME, dev_name)

        if instance is None or namespace is None:
            _LOGGER.error("Skipping %s", dev_name)
            continue

        devices.append(EddystoneTemp(name))

    if devices:
        mon = Monitor(devices, bt_device_id)

        def monitor_stop(_service_or_event):
            """Stop the monitor thread."""
            _LOGGER.info("Stopping scanner for Eddystone beacons")
            mon.stop()

        def monitor_start(_service_or_event):
            """Start the monitor thread."""
            _LOGGER.info("Starting scanner for Eddystone beacons")
            mon.start()

        add_entities(devices)
        mon.start()
        hass.bus.listen_once(EVENT_HOMEASSISTANT_STOP, monitor_stop)
        hass.bus.listen_once(EVENT_HOMEASSISTANT_START, monitor_start)
    else:
        _LOGGER.warning("No devices were added")


def get_from_conf(config, config_key, length):
    """Retrieve value from config and validate length."""
    string = config.get(config_key)
    if len(string) != length:
        _LOGGER.error(
            "Error in configuration parameter %s: Must be exactly %d "
            "bytes. Device will not be added",
            config_key,
            length / 2,
        )
        return None
    return string


class EddystoneTemp(SensorEntity):
    """Representation of a temperature sensor."""

    _attr_should_poll = False
    _attr_unit_of_measurement = TEMP_CELSIUS

    def __init__(self, name):
        """Initialize a sensor."""
        self._attr_name = name
        self.temperature = STATE_UNKNOWN

    @property
    def state(self):
        """Return the state of the device."""
        return self.temperature


class Monitor:
    """Continuously scan for BLE advertisements."""

    def __init__(self, devices, bt_device_id):
        """Construct interface object."""
        # List of beacons to monitor
        self.devices = devices

        def callback(_, __, packet, additional_info):
            """Handle new packets."""
            self.process_packet(
                additional_info["namespace"],
                additional_info["instance"],
                packet.temperature,
            )

        device_filters = [EddystoneFilter(d.namespace, d.instance) for d in devices]

        self.scanner = BeaconScanner(
            callback, bt_device_id, device_filters, EddystoneTLMFrame
        )
        self.scanning = False

    def start(self):
        """Continuously scan for BLE advertisements."""
        if not self.scanning:
            self.scanner.start()
            self.scanning = True
        else:
            _LOGGER.debug("start() called, but scanner is already running")

    def process_packet(self, namespace, instance, temperature):
        """Assign temperature to device."""
        _LOGGER.debug(
            "Received temperature for <%s,%s>: %d", namespace, instance, temperature
        )

        for dev in self.devices:
            if (
                dev.namespace == namespace
                and dev.instance == instance
                and dev.temperature != temperature
            ):
                dev.temperature = temperature
                dev.schedule_update_ha_state()

    def stop(self):
        """Signal runner to stop and join thread."""
        if self.scanning:
            _LOGGER.debug("Stopping")
            self.scanner.stop()
            _LOGGER.debug("Stopped")
            self.scanning = False
        else:
            _LOGGER.debug("stop() called but scanner was not running")

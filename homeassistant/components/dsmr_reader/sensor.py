"""Support for DSMR Reader through MQTT."""
from homeassistant.components import mqtt
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import callback
from homeassistant.util import slugify

from .definitions import DEFINITIONS

DOMAIN = "dsmr_reader"


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up DSMR Reader sensors."""

    sensors = []
    for topic in DEFINITIONS:
        sensors.append(DSMRSensor(topic))

    async_add_entities(sensors)


class DSMRSensor(SensorEntity):
    """Representation of a DSMR sensor that is updated via MQTT."""

    def __init__(self, topic):
        """Initialize the sensor."""

        definition = DEFINITIONS[topic]

        self._entity_id = slugify(topic.replace("/", "_"))
        self._topic = topic

        self._attr_name = definition.get("name", topic.split("/")[-1])
        self._attr_device_class = definition.get("device_class")
        self._attr_enable_default = definition.get("enable_default")
        self._attr_unit_of_measurement = definition.get("unit")
        self._attr_icon = definition.get("icon")
        self._transform = definition.get("transform")
        self._state = None

    async def async_added_to_hass(self):
        """Subscribe to MQTT events."""

        @callback
        def message_received(message):
            """Handle new MQTT messages."""

            if self._transform is not None:
                self._state = self._transform(message.payload)
            else:
                self._state = message.payload

            self.async_write_ha_state()

        await mqtt.async_subscribe(self.hass, self._topic, message_received, 1)

    @property
    def entity_id(self):
        """Return the entity ID for this sensor."""
        return f"sensor.{self._entity_id}"

    @property
    def state(self):
        """Return the current state of the entity."""
        return self._state

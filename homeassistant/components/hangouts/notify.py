"""Support for Hangouts notifications."""
from homeassistant.components.notify import (
    ATTR_DATA,
    ATTR_MESSAGE,
    ATTR_TARGET,
    BaseNotificationService,
)

from .const import DOMAIN, SERVICE_SEND_MESSAGE


class HangoutsNotificationService(BaseNotificationService):
    """Send Notifications to Hangouts conversations."""

    def __init__(self, default_conversations):
        """Set up the notification service."""
        self._default_conversations = default_conversations

    def send_message(self, message="", **kwargs):
        """Send the message to the Google Hangouts server."""
        target_conversations = None
        if ATTR_TARGET in kwargs:
            target_conversations = []
            for target in kwargs.get(ATTR_TARGET):
                target_conversations.append({"id": target})
        else:
            target_conversations = self._default_conversations

        messages = []
        if "title" in kwargs:
            messages.append({"text": kwargs["title"], "is_bold": True})

        messages.append({"text": message, "parse_str": True})
        service_data = {ATTR_TARGET: target_conversations, ATTR_MESSAGE: messages}
        if kwargs[ATTR_DATA]:
            service_data[ATTR_DATA] = kwargs[ATTR_DATA]

        return self.hass.services.call(
            DOMAIN, SERVICE_SEND_MESSAGE, service_data=service_data
        )

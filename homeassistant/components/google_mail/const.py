"""Constants for Google Mail integration."""
from __future__ import annotations

from typing import Final

ATTR_ENABLED = "enabled"
ATTR_END = "end"
ATTR_MESSAGE = "message"
ATTR_PLAIN_TEXT = "plain_text"
ATTR_RESTRICT_CONTACTS = "restrict_contacts"
ATTR_RESTRICT_DOMAIN = "restrict_domain"
ATTR_START = "start"
ATTR_TITLE = "title"

DOMAIN = "google_mail"

DATA_CONFIG_ENTRY: Final = "config_entry"
MANUFACTURER = "Google, Inc."
DEFAULT_ACCESS = ["https://mail.google.com/", "https://www.googleapis.com/auth/gmail.settings.basic"]

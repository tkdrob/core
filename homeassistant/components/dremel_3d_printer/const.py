"""Constants for the Dremel 3D Printer (3D20, 3D40, 3D45) integration."""
from __future__ import annotations

import logging

LOGGER = logging.getLogger(__package__)

DOMAIN = "dremel_3d_printer"

SERVICE_PRINT_JOB = "print_job"
ATTR_FILEPATH = "file_path"
ATTR_URL = "url"
ATTR_DEVICE_ID = "device_id"

EVENT_DATA_NEW_PRINT_STATS = "dremel_3d_printer_new_print_stats"

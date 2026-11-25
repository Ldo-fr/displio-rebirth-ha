"""Constants for the Displio Rebirth integration."""

from __future__ import annotations

DOMAIN = "displio_rebirth"

DEFAULT_PORT = 80
DEFAULT_SCAN_INTERVAL = 30  # seconds
DEFAULT_TIMEOUT = 10  # seconds

CONF_SCAN_INTERVAL = "scan_interval"

EPD_WIDTH = 264
EPD_HEIGHT = 176
EPD_FB_SIZE = (EPD_WIDTH // 8) * EPD_HEIGHT  # 5808 bytes

ORIENTATION_MAP: dict[int, str] = {
    0: "portrait_up",
    1: "portrait_down",
    2: "landscape_right",
    3: "landscape_left",
}

SERVICE_DISPLAY_TEXT = "display_text"
SERVICE_DISPLAY_IMAGE = "display_image"
SERVICE_BEEP = "beep"

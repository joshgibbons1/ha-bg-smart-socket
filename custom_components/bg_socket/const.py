"""Constants for the BG Smart Socket integration."""

from datetime import timedelta

DOMAIN = "bg_socket"

CONF_DEVTYPE = "devtype"
CONF_MANUFACTURER = "manufacturer"
CONF_MODEL = "model"

SCAN_INTERVAL = timedelta(seconds=10)

OUTLETS = (1, 2)

# Lock flags in the device state; cleared while an outlet is switched, then restored.
LOCK_KEYS = ("childlock", "childlock1", "childlock2")

# Auto-off timers are stored in seconds (60 to 86340, 0 = off) and shown in minutes.
TIMER_SECONDS_PER_UNIT = 60
TIMER_MAX_UNITS = 1439

# Indicator LED brightness; values above 100 have no visible effect.
LED_MAX = 100

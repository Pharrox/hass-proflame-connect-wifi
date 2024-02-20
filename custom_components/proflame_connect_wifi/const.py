"""Constants for the Proflame integration."""
from enum import IntEnum, StrEnum

from .util import Temperature


class ApiAttrs(StrEnum):
    """Available attributes accessible via the API."""

    AUXILIARY = "auxiliary_out"
    BURNER_STATUS = "burner_status"
    CURRENT_TEMPERATURE = "room_temperature"
    FAN_SPEED = "fan_control"
    FIRMWARE_REVISION = "fw_revision"
    FLAME_HEIGHT = "flame_control"
    FREE_HEAP = "free_heap"
    LIGHT_BRIGHTNESS = "lamp_control"
    MIN_FREE_HEAP = "min_free_heap"
    OPERATING_MODE = "main_mode"
    PILOT_MODE = "pilot_mode"
    REMOTE_CONTROL = "remote_control"
    SPLIT_FLOW = "split_flow"
    TARGET_TEMPERATURE = "temperature_set"
    TEMPERATURE_UNIT = "temperature_unit"
    WIFI_SIGNAL_STR = "wifi_signal_str"


class ApiControl(StrEnum):
    """Known control messages used by the API."""

    CONN_ACK = "PROFLAMECONNECTIONOPEN"
    CONN_SYN = "PROFLAMECONNECTION"
    PING = "PROFLAMEPING"
    PONG = "PROFLAMEPONG"


class OperatingMode(IntEnum):
    """Available operating modes for fireplace unit."""

    OFF = 0
    MANUAL = 1
    THERMOSTAT = 2
    SMART = 3


class PilotMode(IntEnum):
    """Available pilot modes for the fireplace."""

    INTERMITENT = 0
    CONTINUOUS = 1


class Preset(StrEnum):
    """Available presets for fireplace control."""

    OFF = "Off"
    MANUAL = "Manual"
    THERMOSTAT = "Thermostat"
    SMART = "Smart"


DOMAIN = "proflame_connect_wifi"

DEFAULT_DEVICE = 'Proflame Fireplace'
DEFAULT_NAME = 'Fireplace'
DEFAULT_PORT = 88

PROFLAME_CLIENT = "client"
PROFLAME_COORDINATOR = "coordinator"

ADJUSTABLE_MODES = [
    OperatingMode.MANUAL,
    OperatingMode.THERMOSTAT,
]

MAX_FAN_SPEED = 6
MIN_FAN_SPEED = 0

MAX_FLAME_HEIGHT = 6
MIN_FLAME_HEIGHT = 0

MAX_LIGHT_BRIGHTNESS = 6
MIN_LIGHT_BRIGHTNESS = 0

MAX_TEMPERATURE: Temperature = Temperature.celcius(35)
MIN_TEMPERATURE: Temperature = Temperature.celcius(5)

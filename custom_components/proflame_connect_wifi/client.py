"""Provides high level abstractions for interacting with Proflame fireplaces."""
from homeassistant.components.climate import HVACAction, HVACMode, UnitOfTemperature

from .client_base import ProflameClientBase
from .const import (
    ADJUSTABLE_MODES,
    MAX_FAN_SPEED,
    MAX_FLAME_HEIGHT,
    MAX_LIGHT_BRIGHTNESS,
    MIN_FAN_SPEED,
    MIN_FLAME_HEIGHT,
    MIN_LIGHT_BRIGHTNESS,
    ApiAttrs,
    OperatingMode,
    PilotMode,
    Preset,
)
from .util import Temperature, constrain


class ProflameClient(ProflameClientBase):
    """Client used for interacting with Proflame fireplaces."""

    def __init__(self, device_id, host, port=None, logger=None) -> None:
        """Create new class instance."""
        super().__init__(device_id, host, port, logger)
        self._stored_fan_speed = MAX_FAN_SPEED
        self._stored_flame = MAX_FLAME_HEIGHT
        self._stored_light_brightness = MAX_LIGHT_BRIGHTNESS
        self._stored_mode = OperatingMode.MANUAL
        self._stored_mode_adjustable = OperatingMode.MANUAL
        self.register_callback(self._track_state)

    def _track_state(self, key, value) -> None:
        """Track specific state changes to provide enhanced functionality."""
        if key == ApiAttrs.FAN_SPEED and value > 0:
            self._stored_fan_speed = value
        if key == ApiAttrs.FLAME_HEIGHT and value > 0:
            self._stored_flame = value
        if key == ApiAttrs.LIGHT_BRIGHTNESS and value > 0:
            self._stored_light_brightness = value
        if key == ApiAttrs.OPERATING_MODE and value > 0:
            if not (value == OperatingMode.MANUAL and self.flame_height == 0):
                self._stored_mode = value
            if value in ADJUSTABLE_MODES and self.flame_height != 0:
                self._stored_mode_adjustable = value

    @property
    def current_temperature(self) -> float | None:
        """Get the current temperature reported by the unit."""
        temperature = self.get_state(ApiAttrs.CURRENT_TEMPERATURE)
        if temperature:
            return temperature / 10
        return None

    @property
    def fan_speed(self) -> int:
        """Get the current state of the fan."""
        if self.operating_mode in [None, OperatingMode.OFF]:
            return 0
        return self.get_state(ApiAttrs.FAN_SPEED)

    @property
    def flame_height(self) -> int | None:
        """Get the configured height of the flame."""
        if self.operating_mode in [None, 0]:
            return 0
        return self.get_state(ApiAttrs.FLAME_HEIGHT)

    @property
    def hvac_action(self) -> HVACAction | None:
        """Get the current HVAC heating status."""
        if self.preset == Preset.OFF:
            return HVACAction.OFF
        return HVACAction.HEATING

    @property
    def hvac_mode(self) -> HVACMode | None:
        """Get the current HVAC heating status."""
        if self.preset == Preset.OFF:
            return HVACMode.OFF
        return HVACMode.HEAT

    @property
    def light_brightness(self) -> int | None:
        """Get the current state of the primary light."""
        if self.operating_mode in [None, OperatingMode.OFF]:
            return 0
        return self.get_state(ApiAttrs.LIGHT_BRIGHTNESS)

    @property
    def operating_mode(self) -> OperatingMode | None:
        """Get the current low level operating mode of the fireplace."""
        return self.get_state(ApiAttrs.OPERATING_MODE)

    @property
    def pilot_mode(self) -> PilotMode | None:
        """Get the current pilot mode of the fireplace."""
        return self.get_state(ApiAttrs.PILOT_MODE)

    @property
    def preset(self) -> Preset | None:
        """Get the current state of the fireplace as represented by a preset."""
        cur_mode = self.operating_mode
        if cur_mode == OperatingMode.OFF:
            return Preset.OFF
        if cur_mode == OperatingMode.MANUAL and self.flame_height == 0:
            return Preset.OFF
        if cur_mode == OperatingMode.MANUAL:
            return Preset.MANUAL
        if cur_mode == OperatingMode.THERMOSTAT:
            return Preset.THERMOSTAT
        if cur_mode == OperatingMode.SMART:
            return Preset.SMART

    @property
    def target_temperature(self) -> float | None:
        """The current temperature the device is trying to hit."""
        temperature = self.get_state(ApiAttrs.TARGET_TEMPERATURE)
        if self.preset in [Preset.MANUAL, Preset.OFF]:
            return None
        if temperature:
            return temperature / 10
        return None

    @property
    def temperature_unit(self) -> UnitOfTemperature:
        """The temperature unit the device is configured for."""
        unit = self.get_state(ApiAttrs.TEMPERATURE_UNIT) or 0
        if unit == 0:
            return UnitOfTemperature.CELSIUS
        return UnitOfTemperature.FAHRENHEIT

    def heat(self) -> None:
        """Set the fireplace to the last heat generating configuration."""
        if self.preset != Preset.OFF:
            return
        self.set_operating_mode(self._stored_mode)
        self.set_flame_height(self._stored_flame)

    def is_on(self) -> bool | None:
        """Return true if the fireplace is on."""
        mode = self.operating_mode
        return None if mode is None else bool(mode)

    def set_fan_speed(self, speed: int) -> None:
        """Set the desired speed of the fan."""
        constrained = constrain(speed, MIN_FAN_SPEED, MAX_FAN_SPEED)
        self.set_state(ApiAttrs.FAN_SPEED, constrained)

    def set_flame_height(self, height: int) -> None:
        """Set the height of the flame in manual mode."""
        constrained = constrain(height, MIN_FLAME_HEIGHT, MAX_FLAME_HEIGHT)
        self.set_state(ApiAttrs.FLAME_HEIGHT, constrained)
        if constrained > 0 and self.operating_mode not in ADJUSTABLE_MODES:
            self.set_operating_mode(self._stored_mode_adjustable)

    def set_light_brightness(self, brightness: int) -> None:
        """Set the brightness of the primary light."""
        constrained = constrain(brightness, MAX_LIGHT_BRIGHTNESS, MIN_LIGHT_BRIGHTNESS)
        self.set_state(ApiAttrs.LIGHT_BRIGHTNESS, constrained)

    def set_operating_mode(self, mode: OperatingMode) -> None:
        """Set the primary operating mode of the device."""
        self.set_state(ApiAttrs.OPERATING_MODE, mode)

    def set_pilot_mode(self, mode: PilotMode) -> None:
        """Set the fireplace pilot mode."""
        self.set_state(ApiAttrs.PILOT_MODE, mode)

    def set_preset(self, preset: Preset):
        """Set the fireplace state based on a preset."""
        if preset == Preset.OFF:
            if self.operating_mode != OperatingMode.OFF:
                self.set_flame_height(0)
                self.set_operating_mode(OperatingMode.MANUAL)
        if preset == Preset.MANUAL:
            if self.flame_height == 0:
                self.set_flame_height(self._stored_flame)
            self.set_operating_mode(OperatingMode.MANUAL)
        if preset == Preset.THERMOSTAT:
            self.set_operating_mode(OperatingMode.THERMOSTAT)
        if preset == Preset.SMART:
            self.set_operating_mode(OperatingMode.SMART)

    def set_target_temperature(self, temperature: Temperature) -> None:
        """Set the desired temperature for themostat based modes."""
        if self.temperature_unit == UnitOfTemperature.CELSIUS:
            self.set_state(ApiAttrs.TARGET_TEMPERATURE, int(temperature.to_celcius() * 10))
        if self.temperature_unit == UnitOfTemperature.FAHRENHEIT:
            self.set_state(ApiAttrs.TARGET_TEMPERATURE, int(temperature.to_fahrenheit() * 10))

    def turn_off(self):
        """Turn off full device."""
        self.set_operating_mode(OperatingMode.OFF)

    def turn_off_fan(self):
        """Set fan speed to 0."""
        self.set_fan_speed(0)

    def turn_off_light(self):
        """Set primary light brightness to 0."""
        self.set_light_brightness(0)

    def turn_on(self):
        """Turn on full device."""
        self.set_operating_mode(self._stored_mode)

    def turn_on_fan(self):
        """Set fan speed to last active speed."""
        self.set_fan_speed(self._stored_fan_speed)

    def turn_on_light(self):
        """Set primary light to last active brightness."""
        self.set_light_brightness(self._stored_light_brightness)

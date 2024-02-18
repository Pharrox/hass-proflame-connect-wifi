"""Provides light control for Proflame fireplaces."""
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityDescription,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
    UnitOfTemperature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .client import Temperature
from .const import (
    DOMAIN,
    MAX_TEMPERATURE,
    MIN_TEMPERATURE,
    PROFLAME_COORDINATOR,
    Preset,
)
from .coordinator import ProflameDataCoordinator
from .entity import ProflameEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create the number for Proflame fireplaces."""
    entry_id = config_entry.entry_id
    coordinator: ProflameDataCoordinator = hass.data[DOMAIN][entry_id][PROFLAME_COORDINATOR]
    climate = ProflameClimate(coordinator)
    async_add_entities([climate])

class ProflameClimate(ProflameEntity, ClimateEntity):
    """Creates a device to control fireplace lights."""

    _attr_hvac_modes = [
        HVACMode.HEAT,
        HVACMode.OFF,
    ]
    _attr_preset_modes = [
        'Off',
        'Manual',
        'Thermostat',
        'Smart'
    ]
    _attr_supported_features = (
        ClimateEntityFeature.PRESET_MODE |
        ClimateEntityFeature.TARGET_TEMPERATURE
    )
    _attr_target_temperature_step = 1.0

    def __init__(self, coordinator: ProflameDataCoordinator) -> None:
        """Create new instance of the ProflameFlame class."""
        super().__init__(coordinator, ClimateEntityDescription(
            key='climate',
            translation_key='climate',
        ))

    @property
    def current_temperature(self) -> float | None:
        """Return the current fireplace mode."""
        return self._device.current_temperature

    @property
    def hvac_action(self) -> HVACAction | None:
        """Return the current fireplace mode."""
        return self._device.hvac_action

    @property
    def hvac_mode(self) -> HVACMode | None:
        """Return the current fireplace mode."""
        return self._device.hvac_mode

    @property
    def max_temp(self) -> float:
        """Return the maximum temperature."""
        if self._device.temperature_unit == UnitOfTemperature.FAHRENHEIT:
            return MAX_TEMPERATURE.to_fahrenheit()
        return MAX_TEMPERATURE.to_celcius()

    @property
    def min_temp(self) -> float:
        """Return the minimum temperature."""
        if self._device.temperature_unit == UnitOfTemperature.FAHRENHEIT:
            return MIN_TEMPERATURE.to_fahrenheit()
        return MIN_TEMPERATURE.to_celcius()

    @property
    def preset_mode(self) -> str | None:
        """Return the current fireplace mode."""
        return self._device.preset

    @property
    def target_temperature(self) -> float | None:
        """Return the current fireplace mode."""
        return self._device.target_temperature

    @property
    def temperature_unit(self) -> str:
        """Return the unit of measurement used by the platform."""
        return self._device.temperature_unit

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        temperature = kwargs.get('temperature', None)
        if temperature is None or self.temperature_unit is None:
            return
        if self.temperature_unit == UnitOfTemperature.CELSIUS:
            self._device.set_target_temperature(Temperature.celcius(temperature))
        if self.temperature_unit == UnitOfTemperature.FAHRENHEIT:
            self._device.set_target_temperature(Temperature.fahrenheit(temperature))

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        if hvac_mode == HVACMode.OFF:
            self._device.set_preset(Preset.OFF)
        if hvac_mode == HVACMode.HEAT:
            self._device.heat()

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set new preset mode."""
        if preset_mode == 'Off':
            self._device.set_preset(Preset.OFF)
        if preset_mode == 'Manual':
            self._device.set_preset(Preset.MANUAL)
        if preset_mode == 'Thermostat':
            self._device.set_preset(Preset.THERMOSTAT)
        if preset_mode == 'Smart':
            self._device.set_preset(Preset.SMART)

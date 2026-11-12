"""Provides light control for Proflame fireplaces."""
from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MAX_FLAME_HEIGHT, MIN_FLAME_HEIGHT, PROFLAME_COORDINATOR
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
    flame = ProflameFlame(coordinator)
    async_add_entities([flame])

class ProflameFlame(ProflameEntity, NumberEntity):
    """Creates a device to control fireplace lights."""

    _attr_native_max_value: float = MAX_FLAME_HEIGHT
    _attr_native_min_value: float = MIN_FLAME_HEIGHT
    _attr_native_step: float = 1
    _attr_mode: NumberMode = NumberMode.SLIDER

    def __init__(self, coordinator: ProflameDataCoordinator) -> None:
        """Create new instance of the ProflameFlame class."""
        super().__init__(coordinator, NumberEntityDescription(
            icon='mdi:fire',
            key='burner',
            translation_key='burner',
        ))

    @property
    def native_value(self) -> float | None:
        """Returns the current flame height."""
        return self._device.flame_height

    async def async_set_native_value(self, value: float) -> None:
        """Update the desired height of the flame."""
        self._device.set_flame_height(int(value))

"""Provides light control for Proflame fireplaces."""
import math
from typing import Any

from homeassistant.components.light import (
    ColorMode,
    LightEntity,
    LightEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MAX_LIGHT_BRIGHTNESS, PROFLAME_COORDINATOR
from .coordinator import ProflameDataCoordinator
from .entity import ProflameEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create the lights for Proflame fireplaces."""
    entry_id = config_entry.entry_id
    coordinator: ProflameDataCoordinator = hass.data[DOMAIN][entry_id][PROFLAME_COORDINATOR]
    light = ProflameLight(coordinator)
    async_add_entities([light])

class ProflameLight(ProflameEntity, LightEntity):
    """Creates a device to control fireplace lights."""

    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}

    def __init__(self, coordinator: ProflameDataCoordinator) -> None:
        """Create new instance of the ProflameLight class."""
        super().__init__(coordinator, LightEntityDescription(
            key='light',
            translation_key='light',
        ))

    @property
    def brightness(self) -> int | None:
        """Return the current primary light brightness."""
        brightness = self._device.light_brightness
        if brightness is None:
            return None
        return brightness * int(255 / MAX_LIGHT_BRIGHTNESS)

    @property
    def is_on(self) -> bool | None:
        """Return true if the primary light is on."""
        brightness = self.brightness
        return None if brightness is None else brightness

    def turn_on(self, **kwargs: Any) -> None:
        """Turn the primary light on."""
        brightness = kwargs.get('brightness', None)
        if brightness is None:
            self._device.turn_on_light()
        converted = math.ceil(brightness / (255 / MAX_LIGHT_BRIGHTNESS))
        self._device.set_light_brightness(converted)

    def turn_off(self, **kwargs: Any) -> None:
        """Turn the primary light off."""
        self._device.set_light_brightness(0)

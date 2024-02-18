"""Provides light control for Proflame fireplaces."""
from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, PROFLAME_COORDINATOR, ApiAttrs
from .coordinator import ProflameDataCoordinator
from .entity import ProflameEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create sensors for Proflame fireplaces."""
    entry_id = config_entry.entry_id
    coordinator: ProflameDataCoordinator = hass.data[DOMAIN][entry_id][PROFLAME_COORDINATOR]
    async_add_entities(x for x in [
        ProflameSensor(coordinator, ApiAttrs.FREE_HEAP, 'mdi:code-block-tags'),
        ProflameSensor(coordinator, ApiAttrs.MIN_FREE_HEAP, 'mdi:code-block-tags'),
        ProflameSensor(coordinator, ApiAttrs.WIFI_SIGNAL_STR, 'mdi:wifi'),
    ])

class ProflameSensor(ProflameEntity, SensorEntity):
    """Creates a sensore for Proflame fireplaces."""

    def __init__(
        self,
        coordinator: ProflameDataCoordinator,
        api_attr: ApiAttrs,
        icon: str = None,
    ) -> None:
        """Create new instance of the ProflameSensor class."""
        super().__init__(coordinator, SensorEntityDescription(
            icon=icon,
            key=api_attr,
            translation_key=api_attr,
        ))
        self._api_attr = api_attr

    @property
    def native_value(self) -> bool | None:
        """Return the state of the sensor."""
        return self._device.get_state(self._api_attr)

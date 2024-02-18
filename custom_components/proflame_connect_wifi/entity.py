"""Generic base class for Proflame entities."""
import logging

from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import ProflameDataCoordinator

_LOGGER = logging.getLogger(__name__)


class ProflameEntity(CoordinatorEntity):
    """Generic base class for proflame entities."""

    def __init__(
        self,
        coordinator: ProflameDataCoordinator,
        description: EntityDescription,
    ) -> None:
        """Create new instance of the ProflamEntity class."""
        super().__init__(coordinator)
        self.entity_description = description
        self._device = coordinator.client
        self._attr_device_info = coordinator.device_info
        self._attr_has_entity_name = True
        self._attr_should_poll = False
        self._attr_unique_id = f"{description.key}_{coordinator.unique_id}"
        self._logger = _LOGGER

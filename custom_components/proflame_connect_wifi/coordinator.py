"""Data coordinators for proflame integration."""
import logging
import re

from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .client import ProflameClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class ProflameDataCoordinator(DataUpdateCoordinator):
    """Base class for device coordinators."""

    def __init__(self, hass: HomeAssistant, client: ProflameClient, name: str) -> None:
        """Initialize the Proflam coordinator class."""
        super().__init__(
            hass=hass,
            name='devices',
            logger=_LOGGER,
        )
        self.client = client
        self.async_set_updated_data(self.client.full_state)
        self.client.register_callback(self.handle_state_change)
        self.device_name = name
        self.unique_id = re.sub('[^A-Za-z0-9]+', '', client.device_id)
        self.device_info = DeviceInfo(
            identifiers={(DOMAIN, self.client.device_id)},
            manufacturer='Sit Group',
            model='Generic',
            name=self.device_name
        )

    def handle_state_change(self, key: str, value: int) -> None:
        """Pass new data to the underlying coordinator."""
        self.async_set_updated_data(
            data={
                **self.data,
                key: value,
            }
        )

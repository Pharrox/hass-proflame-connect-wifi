"""The Proflame integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry, ConfigType
from homeassistant.const import CONF_IP_ADDRESS, CONF_PORT, Platform
from homeassistant.core import HomeAssistant

from .client import ProflameClient
from .const import DOMAIN, PROFLAME_CLIENT, PROFLAME_COORDINATOR
from .coordinator import ProflameDataCoordinator

PLATFORMS: list[Platform] = [
    Platform.CLIMATE,
    Platform.FAN,
    Platform.LIGHT,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Proflame fireplaces."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Proflame from a config entry."""

    client = ProflameClient(
        device_id=entry.unique_id,
        host=entry.data[CONF_IP_ADDRESS],
        port=entry.data[CONF_PORT],
    )
    await client.open()

    coordinator = ProflameDataCoordinator(hass, client, entry.title)

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        PROFLAME_CLIENT: client,
        PROFLAME_COORDINATOR: coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    client: ProflameClient = hass.data[DOMAIN][entry.entry_id][PROFLAME_CLIENT]
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    await client.close()

    return unload_ok

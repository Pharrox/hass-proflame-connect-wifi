"""Config flow for Proflame."""
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import (
    CONF_IP_ADDRESS,
    CONF_NAME,
    CONF_PORT,
    CONF_UNIQUE_ID,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
)

from .client import ProflameClient
from .const import DEFAULT_PORT, DOMAIN

SCHEMA = vol.Schema({
    vol.Required(CONF_NAME): str,
    vol.Required(CONF_IP_ADDRESS): str,
    vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
    vol.Required(CONF_UNIQUE_ID): str,
})

_LOGGER = logging.getLogger(__name__)


async def validate_input(
    hass: HomeAssistant, data: dict[str, Any]
) -> bool:
    """Validate the input to ensure we can connect."""
    return await ProflameClient.test_connection(
        data[CONF_IP_ADDRESS],
        data[CONF_PORT]
    )


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Proflame fireplace."""

    VERSION = 1
    MINOR_VERSION = 0

    def __init__(self) -> None:
        """Initialize config flow class."""
        self.discovery_info: dict[str, Any] = {}
        self._devices = None

    async def _async_set_unique_id(self, mac: str) -> None:
        """Set the config entry's unique ID based on MAC and validate no duplicates."""
        unique_id = format_mac(mac)
        await self.async_set_unique_id(unique_id)
        if (self.discovery_info):
            self._abort_if_unique_id_configured(
                updates={
                    CONF_IP_ADDRESS: self.discovery_info[CONF_IP_ADDRESS],
                },
            )
            self._async_abort_entries_match(
                match_dict={
                    CONF_IP_ADDRESS: self.discovery_info[CONF_IP_ADDRESS],
                },
            )
        else:
            self._abort_if_unique_id_configured()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle configuration via the UI."""
        if user_input is None:
            return self.async_show_form(
                data_schema=SCHEMA,
                errors={},
                step_id='user'
            )

        connected = await validate_input(self.hass, user_input)
        if not connected:
            _LOGGER.error(
                'Error while connecting to Proflame fireplace: %s:%s',
                user_input[CONF_IP_ADDRESS],
                user_input[CONF_PORT],
            )
            return self.async_show_form(
                step_id='user',
                data_schema=SCHEMA,
                errors={CONF_IP_ADDRESS: 'cannot_connect'}
            )

        await self._async_set_unique_id(user_input[CONF_UNIQUE_ID])

        return self.async_create_entry(
            data=user_input,
            title=user_input[CONF_NAME],
        )

    #async def async_step_dhcp(
    #    self, discovery_info: dhcp.DhcpServiceInfo
    #) -> FlowResult:
    #    """Handle configuration via the UI."""
    #    self.discovery_info = {
    #        CONF_IP_ADDRESS: discovery_info.ip,
    #        CONF_MAC: discovery_info.macaddress,
    #        CONF_PORT: DEFAULT_PORT,
    #    }
    #    await self._async_set_unique_id(discovery_info.macaddress)

    #    self.context[CONF_IP_ADDRESS] = discovery_info.ip
    #    in_flight = [x['context'][CONF_IP_ADDRESS] for x in self._async_in_progress()]
    #    if discovery_info.ip in in_flight:
    #        return self.async_abort(reason="already_in_progress")

    #    return await self.async_step_discovery_confirm()

#async def _async_has_devices(hass: HomeAssistant) -> bool:
#    """Return if there are devices that can be discovered."""
#    devices = await hass.async_add_executor_job(my_pypi_dependency.discover)
#    return len(devices) > 0


#config_entry_flow.register_discovery_flow(DOMAIN, "Proflame", _async_has_devices)

"""Config flow for Proflame."""
import logging
import socket
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import dhcp
from homeassistant.const import (
    CONF_HOST,
    CONF_IP_ADDRESS,
    CONF_NAME,
    CONF_PORT,
    CONF_UNIQUE_ID,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.device_registry import format_mac

from .client import ProflameClient
from .const import DEFAULT_DEVICE, DEFAULT_NAME, DEFAULT_PORT, DOMAIN

DISCOVERY_CONFIRM_SCHEMA = vol.Schema({
    vol.Required(CONF_NAME): str,
})

_LOGGER = logging.getLogger(__name__)


def build_user_schema(user_input: dict[str, Any] | None = None):
    """Generate user schema while respecting previously input data."""
    state = user_input or {}
    return vol.Schema({
        vol.Required(CONF_NAME, default=state.get(CONF_NAME, DEFAULT_NAME)): str,
        vol.Required(CONF_HOST, default=state.get(CONF_HOST, None)): str,
        vol.Required(CONF_PORT, default=state.get(CONF_PORT, DEFAULT_PORT)): int,
        vol.Required(CONF_UNIQUE_ID, default=state.get(CONF_UNIQUE_ID, None)): str,
    })

def resolve_host(ip) -> str:
    """Try to get a DNS name from an IP address with verification of forward resolution."""
    try:
        host = socket.getnameinfo((ip, 0), 0)[0]
        resolved = [x[4][0] for x in socket.getaddrinfo(
            host=host,
            port=None,
            proto=6,
        )]
        return host if ip in resolved else ip
    except socket.gaierror:
        # Host from rDNS isn't forward resolvable
        return ip

async def test_connectivity(host: str, port: int = DEFAULT_PORT) -> bool:
    """Validate fireplace is connectable."""
    return await ProflameClient.test_connection(host, port)

async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> bool:
    """Validate user input."""
    return await test_connectivity(data[CONF_HOST], data[CONF_PORT],)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Proflame fireplace."""

    VERSION = 1
    MINOR_VERSION = 0

    @property
    def _device(self):
        host = self.context.get(CONF_HOST, None)
        ip = self.context.get(CONF_IP_ADDRESS, None)
        if host is not None and ip is not None and host != ip:
            return f"{host} ({ip})"
        if host is None and ip is not None:
            return ip
        return DEFAULT_DEVICE

    async def _async_set_unique_id(self, unique_id: str) -> None:
        """Set the config entry's unique ID and validate no duplicates."""
        await self.async_set_unique_id(unique_id)
        if (self.context.get(CONF_HOST, None)):
            self._abort_if_unique_id_configured(
                updates={
                    CONF_HOST: self.context[CONF_HOST],
                },
            )
            self._async_abort_entries_match(
                match_dict={
                    CONF_HOST: self.context[CONF_HOST],
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
                data_schema=build_user_schema(),
                errors={},
                step_id='user'
            )

        connected = await validate_input(self.hass, user_input)
        if not connected:
            _LOGGER.error(
                'Error while connecting to Proflame fireplace: %s:%s',
                user_input[CONF_HOST],
                user_input[CONF_PORT],
            )
            return self.async_show_form(
                step_id='user',
                data_schema=build_user_schema(user_input),
                errors={CONF_HOST: 'cannot_connect'}
            )

        await self._async_set_unique_id(user_input[CONF_UNIQUE_ID])
        return self.async_create_entry(
            data=user_input,
            title=user_input[CONF_NAME],
        )

    async def async_step_dhcp(
        self, discovery_info: dhcp.DhcpServiceInfo
    ) -> FlowResult:
        """Handle configuration via the UI."""
        await self._async_set_unique_id(format_mac(discovery_info.macaddress))

        self.context[CONF_HOST] = resolve_host(discovery_info.ip)
        self.context[CONF_IP_ADDRESS] = discovery_info.ip
        in_flight = [x['context'][CONF_IP_ADDRESS] for x in self._async_in_progress()]
        if discovery_info.ip in in_flight:
            return self.async_abort(reason="already_in_progress")

        return await self.async_step_discovery_confirm()

    async def async_step_discovery_confirm(self, user_input=None):
        """Confirm discovery."""
        if user_input is not None:
            return self.async_create_entry(
                data={
                    CONF_NAME: user_input[CONF_NAME],
                    CONF_IP_ADDRESS: self.context[CONF_IP_ADDRESS],
                    CONF_PORT: DEFAULT_PORT,
                    CONF_UNIQUE_ID: self.unique_id
                },
                title=user_input[CONF_NAME],
            )

        self.context["title_placeholders"] = {'device': self._device}
        return self.async_show_form(
            data_schema=DISCOVERY_CONFIRM_SCHEMA,
            description_placeholders=self.context["title_placeholders"],
            errors={},
            step_id='discovery_confirm'
        )

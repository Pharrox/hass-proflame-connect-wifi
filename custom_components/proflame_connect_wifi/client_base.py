"""Low level functionality for interacting with Proflame fireplaces."""
import asyncio
import json
from json.decoder import JSONDecodeError
import logging

from websockets import ConnectionClosed, ConnectionClosedError
from websockets.client import connect

from .const import DEFAULT_PORT, ApiControl

_LOGGER = logging.getLogger(__name__)


class ProflameClientBase:
    """Client used for interacting with Proflame fireplaces."""

    @staticmethod
    async def test_connection(host: str, port: int | None = None) -> bool:
        """Test the connection to the fireplace."""

        try:
            uri = f"ws://{host}:{port or DEFAULT_PORT}"
            async with connect(uri) as ws:
                await ws.send(ApiControl.CONN_SYN)
                response = await ws.recv()

                if response == ApiControl.CONN_ACK:
                    _LOGGER.debug("Proflame connection to '%s' established")
                    return True
                else:
                    msg = "Proflame connection test to '%s' failed with unexpected response (%s)"
                    _LOGGER.error(msg, uri, response)
                    return False
        except Exception: # pylint: disable=broad-exception-caught
            msg = "Encountered error while testing Proflame connection '%s'"
            _LOGGER.exception(msg, uri)
            return False

    def __init__(self, device_id, host, port=None, logger=None, auto_reconnect=True) -> None:
        """Create new class instance."""
        self._auto_reconnect = auto_reconnect
        self._device_id = device_id
        self._host = host
        self._port = port or DEFAULT_PORT
        self._logger = logger or _LOGGER
        self._callbacks = []

        self._ws = None
        self._shutdown = False
        self._queue = asyncio.Queue()
        self._connection = None

        self._state = {}

    def __enter__(self):
        """Initiate a connection for a context manager."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        """Clean up on context manager exit."""
        self.close()

    async def _connect(self):
        """Maintain an open connection to the websocket."""
        tasks = []
        try:
            async for websocket in connect(self.uri, ping_interval=None):
                self._debug('Connection opened')
                try:
                    self._ws = websocket
                    if not tasks:
                        tasks = [
                            asyncio.create_task(self._dispatcher()),
                            asyncio.create_task(self._listener()),
                            asyncio.create_task(self._keepalive()),
                        ]
                    await self._send(ApiControl.CONN_SYN)
                    await asyncio.gather(*tasks, return_exceptions=True)
                except (ConnectionClosed, ConnectionClosedError):
                    msg = 'Attempting to reopen after connection closed unexpectedly'
                    self._warning(msg)
        except asyncio.CancelledError:
            for task in tasks or []:
                task.cancel()

    async def _dispatcher(self) -> None:
        """Handle the sending of messages in an interruption safe way."""
        item = None
        while True:
            try:
                if item is None:
                    item = await self._queue.get()
                await self._send(json.dumps(item))
                self._queue.task_done()
                item = None
            except asyncio.CancelledError:
                break
            except Exception: # pylint: disable=broad-exception-caught
                self._exception('Unexpected error during send')
                await asyncio.sleep(1)

    def _handle_control_message(self, message):
        """Process a system control/info message from the websocket."""
        if message == ApiControl.CONN_ACK:
            self._debug('Connection acknowledged')
        elif message == ApiControl.PONG:
            self._debug('Ping acknowledged')
        else:
            self._warning("Received unexpected control message (%s)", message)

    def _handle_json_message(self, message) -> None:
        """Process a system state message from the websocket."""
        err_msg = "Received unexpected JSON message (%s) - %s"
        if not isinstance(message, dict):
            self._warning(err_msg, "NOT_AN_OBJECT", json.dumps(message))
        elif any(not isinstance(x, int) for x in message.values()):
            self._warning(err_msg, "UNKNOWN_SCHEMA", json.dumps(message))
        else:
            for k, v in message.items():
                self._state[k] = v
                for callback in self._callbacks:
                    callback(k, v)

    def _handle_message(self, message):
        """Process a message from the websocket."""
        try:
            self._handle_json_message(json.loads(message))
        except JSONDecodeError:
            self._handle_control_message(message)

    async def _keepalive(self):
        """Send periodic messages to keep the websocket connection alive."""
        while True:
            try:
                await asyncio.sleep(5)
                await self._send(ApiControl.PING)
            except asyncio.CancelledError:
                break
            except Exception: # pylint: disable=broad-exception-caught
                self._exception('Unexpected error during ping')
                await asyncio.sleep(1)

    async def _listener(self):
        """Handle receiving messages in a connection safe way."""
        while True:
            try:
                async for message in self._ws:
                    self._warning('RECV: %s', message)
                    self._handle_message(message)
            except asyncio.CancelledError:
                break
            except Exception: # pylint: disable=broad-exception-caught
                self._exception('Unexpected error during receive')
                await asyncio.sleep(1)

    async def _send(self, message) -> None:
        """Send message to the fireplace websocket."""
        self._debug("SEND: %s", message)
        await self._ws.send(message)

    async def close(self) -> None:
        """Close the websocket connection."""
        self._debug('Connection closing')
        if self._connection:
            self._connection.cancel()
            await asyncio.gather(self._connection, return_exceptions=True)
            self._connection = None
        if self._ws is not None:
            await self._ws.close()
            self._ws = None
        self._debug('Connection closed')

    def get_state(self, field: str) -> int | None:
        """Query the state of the fireplace."""
        return self._state.get(field, None)

    async def open(self) -> None:
        """Connect to the Proflame websocket."""
        self._warning('Connection opening')
        self._connection = asyncio.create_task(self._connect())

    def register_callback(self, callback) -> None:
        """Register a callback that will be triggered on state changes."""
        self._callbacks.append(callback)

    def set_state(self, field: str, value: int) -> None:
        """Send a state update to the fireplace."""
        self._queue.put_nowait({field: value})

    def _debug(self, msg, *args) -> None:
        """Shortcut for debug logging."""
        formatted = f"PF[{self._host}] {msg}"
        self._logger.debug(formatted, *args)

    def _error(self, msg, *args) -> None:
        """Shortcut for error logging."""
        formatted = f"PF[{self._host}] {msg}"
        self._logger.error(formatted, *args)

    def _exception(self, msg, *args) -> None:
        """Shortcut for exception logging."""
        formatted = f"PF[{self._host}] {msg}"
        self._logger.exception(formatted, *args)

    def _info(self, msg, *args) -> None:
        """Shortcut for info logging."""
        formatted = f"PF[{self._host}] {msg}"
        self._logger.info(formatted, *args)

    def _warning(self, msg, *args) -> None:
        """Shortcut for warning logging."""
        formatted = f"PF[{self._host}] {msg}"
        self._logger.warning(formatted, *args)

    @property
    def device_id(self) -> str:
        """Retrieve the unique ID of the device."""
        return self._device_id

    @property
    def full_state(self) -> dict[str, int]:
        """Retrieve full copy of all know fireplace state."""
        return {**self._state}

    @property
    def uri(self):
        """The formatted URI for connecting to the fireplace websocket."""
        return f"ws://{self._host}:{self._port}"

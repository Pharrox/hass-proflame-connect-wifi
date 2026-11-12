"""Low level functionality for interacting with Proflame fireplaces."""
import asyncio
import json
from json.decoder import JSONDecodeError
import logging
import time

from websockets.client import connect

from .const import (
    DEFAULT_PORT,
    KEEPALIVE_INTERVAL,
    KEEPALIVE_TIMEOUT,
    RECONNECT_DELAY,
    ApiControl,
)

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
        self._connection_callbacks = []

        self._ws = None
        self._connected = False
        self._last_recv = 0.0
        self._queue = asyncio.Queue()
        self._connection = None

        self._state = {}
        self._uses_indexed_format = False
        self._state_received = asyncio.Event()

    def __enter__(self):
        """Initiate a connection for a context manager."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        """Clean up on context manager exit."""
        self.close()

    async def _connect(self):
        """Maintain an open connection to the websocket, reconnecting as needed."""
        dispatcher = asyncio.create_task(self._dispatcher())
        try:
            async for websocket in connect(self.uri, ping_interval=None):
                self._debug('Connection opened')
                self._ws = websocket
                self._last_recv = time.monotonic()
                # Listener and keepalive are bound to this specific connection.
                # When either one finishes, the connection is considered dead.
                tasks = [
                    asyncio.create_task(self._listener(websocket)),
                    asyncio.create_task(self._keepalive(websocket)),
                ]
                try:
                    await websocket.send(ApiControl.CONN_SYN)
                    self._set_connected(True)
                    done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                    for task in done:
                        if not task.cancelled() and task.exception() is not None:
                            self._warning('Connection lost: %s', task.exception())
                except asyncio.CancelledError:
                    raise
                except Exception as err: # pylint: disable=broad-exception-caught
                    self._warning('Connection failed: %s', err)
                finally:
                    self._set_connected(False)
                    self._ws = None
                    for task in tasks:
                        task.cancel()
                    await asyncio.gather(*tasks, return_exceptions=True)
                    await websocket.close()
                self._warning('Reconnecting in %s seconds', RECONNECT_DELAY)
                await asyncio.sleep(RECONNECT_DELAY)
        except asyncio.CancelledError:
            pass
        finally:
            dispatcher.cancel()
            await asyncio.gather(dispatcher, return_exceptions=True)

    def _set_connected(self, connected: bool) -> None:
        """Update connection state and notify listeners on change."""
        if self._connected == connected:
            return
        self._connected = connected
        if not connected:
            # Drop pending commands rather than replaying stale ones on reconnect
            while not self._queue.empty():
                self._queue.get_nowait()
                self._queue.task_done()
        for callback in self._connection_callbacks:
            callback(connected)

    def _format_command(self, item: dict) -> str:
        """Format a command for sending to the fireplace.

        Newer firmware expects: {"control0": "main_mode", "value0": "5", "control1": "attr", "value1": "value"}
        The main_mode: 5 enables WiFi/app control mode.
        Older firmware expects: {"attr": value}
        """
        if self._uses_indexed_format:
            # Convert {attr: value} to include main_mode:5 for WiFi control
            if len(item) == 1:
                attr, value = next(iter(item.items()))
                return json.dumps({
                    "control0": "main_mode",
                    "value0": "5",
                    "control1": attr,
                    "value1": str(value)
                }, separators=(',', ':'))
        # Fall back to simple format for older firmware
        return json.dumps(item, separators=(',', ':'))

    async def _dispatcher(self) -> None:
        """Handle the sending of queued commands."""
        while True:
            item = await self._queue.get()
            try:
                if self._ws is None:
                    self._warning('Dropping command while disconnected (%s)', item)
                else:
                    await self._send(self._format_command(item))
            except asyncio.CancelledError:
                raise
            except Exception as err: # pylint: disable=broad-exception-caught
                # Don't retry: the connection is being re-established, and
                # replaying fireplace commands later could be surprising.
                self._warning('Failed to send command (%s): %s', item, err)
            finally:
                self._queue.task_done()

    def _handle_control_message(self, message):
        """Process a system control/info message from the websocket."""
        if message == ApiControl.CONN_ACK:
            self._debug('Connection acknowledged')
        elif message == ApiControl.PONG:
            self._debug('Ping acknowledged')
        else:
            self._warning("Received unexpected control message (%s)", message)

    def _parse_indexed_format(self, message: dict) -> dict[str, int | str] | None:
        """Parse indexed status/value format used by newer firmware.

        Newer firmware sends: {"status0": "attr", "value0": "123", ...}
        This converts to: {"attr": 123, ...}
        """
        if "status0" not in message:
            return None

        result = {}
        i = 0
        while f"status{i}" in message:
            attr_name = message.get(f"status{i}")
            value_str = message.get(f"value{i}")

            if attr_name is not None and value_str is not None:
                try:
                    result[str(attr_name)] = int(value_str)
                except (ValueError, TypeError):
                    # Store non-numeric values as strings (e.g., firmware versions)
                    result[str(attr_name)] = str(value_str)
            i += 1

        return result if result else None

    def _handle_json_message(self, message) -> None:
        """Process a system state message from the websocket."""
        err_msg = "Received unexpected JSON message (%s) - %s"
        if not isinstance(message, dict):
            self._warning(err_msg, "NOT_AN_OBJECT", json.dumps(message))
            return

        # Try to parse indexed format (status0/value0, status1/value1, etc.)
        parsed = self._parse_indexed_format(message)
        if parsed is not None:
            self._uses_indexed_format = True
            message = parsed
        elif any(not isinstance(x, int) for x in message.values()):
            self._warning(err_msg, "UNKNOWN_SCHEMA", json.dumps(message))
            return

        for k, v in message.items():
            self._state[k] = v
            for callback in self._callbacks:
                callback(k, v)
        # Signal that we've received state (used for protocol detection)
        self._state_received.set()

    def _handle_message(self, message):
        """Process a message from the websocket."""
        try:
            self._handle_json_message(json.loads(message))
        except JSONDecodeError:
            self._handle_control_message(message)

    async def _keepalive(self, websocket) -> None:
        """Ping the device periodically and return if it stops responding.

        Returning (or raising) ends the connection and triggers a reconnect.
        """
        while True:
            await asyncio.sleep(KEEPALIVE_INTERVAL)
            silence = time.monotonic() - self._last_recv
            if silence > KEEPALIVE_TIMEOUT:
                self._warning('No response from device in %.0f seconds', silence)
                return
            self._debug("SEND: %s", ApiControl.PING)
            await websocket.send(ApiControl.PING)

    async def _listener(self, websocket) -> None:
        """Receive messages until the connection closes.

        Connection errors propagate so the connection can be re-established.
        """
        async for message in websocket:
            self._last_recv = time.monotonic()
            self._debug('RECV: %s', message)
            try:
                self._handle_message(message)
            except Exception: # pylint: disable=broad-exception-caught
                self._exception('Unexpected error handling message (%s)', message)
        self._warning('Connection closed by device')

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
        self._debug('Connection closed')

    @property
    def connected(self) -> bool:
        """Return true if the websocket connection is currently open."""
        return self._connected

    def get_state(self, field: str) -> int | None:
        """Query the state of the fireplace."""
        return self._state.get(field, None)

    async def open(self) -> None:
        """Connect to the Proflame websocket."""
        self._debug('Connection opening')
        self._connection = asyncio.create_task(self._connect())

    async def wait_for_state(self, timeout: float = 10.0) -> bool:
        """Wait for state to be received from the device.

        This ensures the device protocol (indexed vs simple) is detected
        before sending any commands.

        :param timeout: Maximum time to wait for state.
        :return: True if state was received, False if timeout.
        """
        try:
            await asyncio.wait_for(self._state_received.wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            self._warning('Timeout waiting for initial state from device')
            return False

    def register_callback(self, callback) -> None:
        """Register a callback that will be triggered on state changes."""
        self._callbacks.append(callback)

    def register_connection_callback(self, callback) -> None:
        """Register a callback that will be triggered on connect/disconnect."""
        self._connection_callbacks.append(callback)

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

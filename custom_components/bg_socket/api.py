"""Local API for BG double sockets (Broadlink "bg1" devices)."""

from __future__ import annotations

from collections.abc import Callable
import threading
import time
from typing import Any

import broadlink
from broadlink.exceptions import BroadlinkException, check_error

from .const import LOCK_KEYS

COMMAND_ID = 0x6A
FLAG_READ = 1
FLAG_WRITE = 2


class BGSocketError(Exception):
    """The socket could not be reached or rejected a command."""


class UnsupportedDeviceError(BGSocketError):
    """The device at the given address is not a BG double socket."""


def probe(host: str) -> dict[str, Any]:
    """Find the device at ``host`` and return what is needed to reconnect later."""
    try:
        device = broadlink.hello(host)
        if not isinstance(device, broadlink.bg1):
            raise UnsupportedDeviceError(f"{host} is not a BG double socket")
        device.auth()
    except (BroadlinkException, OSError) as err:
        raise BGSocketError(f"Could not connect to {host}: {err}") from err

    return {
        "mac": device.mac.hex(),
        "devtype": device.devtype,
        "manufacturer": device.manufacturer,
        "model": device.model,
    }


class BGSocketApi:
    """Blocking client for one socket. Run it in an executor."""

    def __init__(self, host: str, mac: str, devtype: int) -> None:
        self.host = host
        self._lock = threading.Lock()
        self._device = broadlink.gendevice(devtype, (host, 80), bytes.fromhex(mac))

    def connect(self) -> None:
        """Authenticate with the device."""
        with self._lock:
            self._call(self._device.auth)

    def get_state(self) -> dict[str, Any]:
        """Return the full device state."""
        with self._lock:
            return self._call(self._device.get_state)

    def set_state(self, **values: Any) -> dict[str, Any]:
        """Write arbitrary state keys and return the resulting full state."""
        with self._lock:
            return self._call(lambda: self._write(values))

    def set_outlet(self, outlet: int, on: bool) -> dict[str, Any]:
        """Switch an outlet, clearing any child lock first and restoring it afterwards.

        The device ignores power writes while a lock is set. The restore happens
        even if the switch fails.
        """
        key = f"pwr{outlet}"
        target = int(on)
        with self._lock:
            state = self._call(self._device.get_state)
            engaged = {name: 1 for name in LOCK_KEYS if state.get(name)}
            try:
                if engaged:
                    self._call(lambda: self._write({name: 0 for name in engaged}))
                state = self._call(lambda: self._write({key: target}))
                for _ in range(5):
                    if state.get(key) == target:
                        break
                    time.sleep(0.3)
                    state = self._call(self._device.get_state)
                else:
                    raise BGSocketError(f"Outlet {outlet} did not switch")
            finally:
                if engaged:
                    state = self._call(lambda: self._write(engaged))
            return state

    def _write(self, values: dict[str, Any]) -> dict[str, Any]:
        packet = self._device._encode(FLAG_WRITE, values)  # noqa: SLF001
        response = self._device.send_packet(COMMAND_ID, packet)
        check_error(response[0x22:0x24])
        return self._device._decode(response)  # noqa: SLF001

    def _call(self, func: Callable[[], Any]) -> Any:
        """Run ``func``, re-authenticating and retrying once on failure."""
        try:
            try:
                return func()
            except (BroadlinkException, OSError):
                self._device.auth()
                return func()
        except (BroadlinkException, OSError) as err:
            raise BGSocketError(f"Communication with {self.host} failed: {err}") from err

"""Tests for BGSocketApi.set_outlet.

The Broadlink library is replaced with a small fake, so these run without Home
Assistant or real hardware. The fake mimics the behaviour the integration relies
on: power writes are silently ignored while a child lock covers the outlet.
"""

from __future__ import annotations

import importlib
from pathlib import Path
import sys
import types
import unittest
from unittest import mock

PACKAGE_DIR = Path(__file__).resolve().parents[1] / "custom_components" / "bg_socket"
LOCKS = ("childlock", "childlock1", "childlock2")


class _BroadlinkError(Exception):
    pass


class _Response(bytearray):
    result: dict | None = None


class FakeDevice:
    """Behaves like a BG double socket as far as locks and power are concerned."""

    def __init__(self) -> None:
        self.state = {
            "pwr": 0, "pwr1": 0, "pwr2": 0,
            "childlock": 0, "childlock1": 0, "childlock2": 0,
            "maxworktime": 0, "maxworktime1": 0, "maxworktime2": 0,
            "idcbrightness": 19,
        }
        self.ignore_power_writes = False
        self.writes: list[dict] = []

    def auth(self) -> None:
        pass

    def get_state(self) -> dict:
        return dict(self.state)

    def _encode(self, flag: int, state: dict):
        return (flag, dict(state))

    def send_packet(self, command: int, packet) -> _Response:
        _, values = packet
        self.writes.append(dict(values))
        for key, value in values.items():
            if key in ("pwr1", "pwr2"):
                locked = self.state["childlock"] or self.state[f"childlock{key[-1]}"]
                if not locked and not self.ignore_power_writes:
                    self.state[key] = value
                    self.state["pwr"] = int(bool(self.state["pwr1"] or self.state["pwr2"]))
            else:
                self.state[key] = value
        response = _Response(0x40)
        response.result = dict(self.state)
        return response

    def _decode(self, response: _Response) -> dict:
        return response.result


class SetOutletTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        exceptions = types.ModuleType("broadlink.exceptions")
        exceptions.BroadlinkException = _BroadlinkError
        exceptions.check_error = lambda data: None
        broadlink = types.ModuleType("broadlink")
        broadlink.exceptions = exceptions
        broadlink.bg1 = type("bg1", (), {})
        broadlink.gendevice = lambda devtype, address, mac: object()
        package = types.ModuleType("bg_socket_under_test")
        package.__path__ = [str(PACKAGE_DIR)]
        modules = {
            "broadlink": broadlink,
            "broadlink.exceptions": exceptions,
            "bg_socket_under_test": package,
        }
        with mock.patch.dict(sys.modules, modules):
            cls.api_module = importlib.import_module("bg_socket_under_test.api")

    def setUp(self) -> None:
        self.device = FakeDevice()
        self.api = self.api_module.BGSocketApi("192.0.2.1", "aabbccddeeff", 0x51E3)
        self.api._device = self.device

    def test_switches_through_the_master_lock_and_restores_it(self) -> None:
        self.device.state["childlock"] = 1
        state = self.api.set_outlet(1, True)
        self.assertEqual(state["pwr1"], 1)
        self.assertEqual(state["childlock"], 1)

    def test_only_the_locks_that_were_set_are_restored(self) -> None:
        self.device.state["childlock2"] = 1
        self.device.state["pwr1"] = 1
        self.api.set_outlet(1, False)
        self.assertEqual(self.device.state["pwr1"], 0)
        self.assertEqual(self.device.state["childlock2"], 1)
        self.assertEqual(self.device.state["childlock"], 0)
        self.assertEqual(self.device.state["childlock1"], 0)

    def test_locked_outlet_is_switched_and_relocked(self) -> None:
        self.device.state["childlock2"] = 1
        self.api.set_outlet(2, True)
        self.assertEqual(self.device.state["pwr2"], 1)
        self.assertEqual(self.device.state["childlock2"], 1)

    def test_unlocked_outlet_writes_only_the_power_key(self) -> None:
        self.api.set_outlet(1, True)
        self.assertEqual(self.device.writes, [{"pwr1": 1}])

    def test_failure_raises_and_still_restores_the_lock(self) -> None:
        self.device.state["childlock"] = 1
        self.device.state["pwr1"] = 1
        self.device.ignore_power_writes = True
        with mock.patch.object(self.api_module.time, "sleep"):
            with self.assertRaises(self.api_module.BGSocketError):
                self.api.set_outlet(1, False)
        self.assertEqual(self.device.state["childlock"], 1)


if __name__ == "__main__":
    unittest.main()

"""On/off switches for the two outlets."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import OUTLETS
from .coordinator import BGSocketConfigEntry, BGSocketCoordinator
from .entity import BGSocketEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BGSocketConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(BGSocketOutlet(coordinator, outlet) for outlet in OUTLETS)


class BGSocketOutlet(BGSocketEntity, SwitchEntity):
    """One outlet. Works through a child lock by lifting and restoring it."""

    _attr_device_class = SwitchDeviceClass.OUTLET

    def __init__(self, coordinator: BGSocketCoordinator, outlet: int) -> None:
        super().__init__(coordinator, f"pwr{outlet}", f"Socket {outlet}")
        self._outlet = outlet

    @property
    def is_on(self) -> bool | None:
        value = self._value
        return None if value is None else bool(value)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_outlet(self._outlet, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_outlet(self._outlet, False)

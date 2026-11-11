"""Per-outlet child locks that freeze an outlet in its current state."""

from __future__ import annotations

from typing import Any

from homeassistant.components.lock import LockEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import BGSocketConfigEntry, BGSocketCoordinator
from .entity import BGSocketEntity

LOCKS = (
    ("childlock1", "Socket 1 child lock"),
    ("childlock2", "Socket 2 child lock"),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BGSocketConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(BGSocketLock(coordinator, key, name) for key, name in LOCKS)


class BGSocketLock(BGSocketEntity, LockEntity):
    """Child lock for one outlet."""

    def __init__(self, coordinator: BGSocketCoordinator, key: str, name: str) -> None:
        super().__init__(coordinator, key, name)

    @property
    def is_locked(self) -> bool | None:
        value = self._value
        return None if value is None else bool(value)

    async def async_lock(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_state(**{self._key: 1})

    async def async_unlock(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_state(**{self._key: 0})

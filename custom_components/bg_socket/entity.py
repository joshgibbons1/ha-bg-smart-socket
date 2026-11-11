"""Base entity for the BG Smart Socket integration."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_MANUFACTURER, CONF_MODEL, DOMAIN
from .coordinator import BGSocketCoordinator


class BGSocketEntity(CoordinatorEntity[BGSocketCoordinator]):
    """An entity backed by one key of the socket's state."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: BGSocketCoordinator, key: str, name: str) -> None:
        super().__init__(coordinator)
        entry = coordinator.config_entry
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"{entry.unique_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.unique_id)},
            name=entry.title,
            manufacturer=entry.data.get(CONF_MANUFACTURER),
            model=entry.data.get(CONF_MODEL),
        )

    @property
    def _value(self) -> Any:
        return self.coordinator.data.get(self._key)

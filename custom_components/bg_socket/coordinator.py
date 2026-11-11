"""Data update coordinator for the BG Smart Socket integration."""

from __future__ import annotations

from collections.abc import Callable
from functools import partial
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import BGSocketApi, BGSocketError
from .const import SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

type BGSocketConfigEntry = ConfigEntry[BGSocketCoordinator]


class BGSocketCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Polls one socket and funnels all writes through a single place."""

    config_entry: BGSocketConfigEntry

    def __init__(
        self, hass: HomeAssistant, entry: BGSocketConfigEntry, api: BGSocketApi
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=entry.title,
            update_interval=SCAN_INTERVAL,
        )
        self.api = api

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.hass.async_add_executor_job(self.api.get_state)
        except BGSocketError as err:
            raise UpdateFailed(str(err)) from err

    async def async_set_state(self, **values: Any) -> None:
        """Write raw state keys (locks, timers, LED brightness)."""
        await self._async_write(self.api.set_state, **values)

    async def async_set_outlet(self, outlet: int, on: bool) -> None:
        """Switch an outlet, unlocking and relocking around it if needed."""
        await self._async_write(self.api.set_outlet, outlet, on)

    async def _async_write(self, func: Callable[..., dict[str, Any]], *args: Any, **kwargs: Any) -> None:
        try:
            state = await self.hass.async_add_executor_job(partial(func, *args, **kwargs))
        except BGSocketError as err:
            raise HomeAssistantError(str(err)) from err
        self.async_set_updated_data(state)

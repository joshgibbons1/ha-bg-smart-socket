"""The BG Smart Socket integration."""

from __future__ import annotations

from homeassistant.const import CONF_HOST, CONF_MAC, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .api import BGSocketApi, BGSocketError
from .const import CONF_DEVTYPE
from .coordinator import BGSocketConfigEntry, BGSocketCoordinator

PLATFORMS = [Platform.LOCK, Platform.NUMBER, Platform.SWITCH]


async def async_setup_entry(hass: HomeAssistant, entry: BGSocketConfigEntry) -> bool:
    """Set up a socket from a config entry."""
    api = BGSocketApi(entry.data[CONF_HOST], entry.data[CONF_MAC], entry.data[CONF_DEVTYPE])
    try:
        await hass.async_add_executor_job(api.connect)
    except BGSocketError as err:
        raise ConfigEntryNotReady(str(err)) from err

    coordinator = BGSocketCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: BGSocketConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

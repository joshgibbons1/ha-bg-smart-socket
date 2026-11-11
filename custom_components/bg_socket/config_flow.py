"""Config flow for the BG Smart Socket integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_NAME

from .api import BGSocketError, UnsupportedDeviceError, probe
from .const import CONF_DEVTYPE, CONF_MANUFACTURER, CONF_MODEL, DOMAIN


class BGSocketConfigFlow(ConfigFlow, domain=DOMAIN):
    """Add a socket by IP address."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            try:
                info = await self.hass.async_add_executor_job(probe, host)
            except UnsupportedDeviceError:
                errors["base"] = "unsupported"
            except BGSocketError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(info["mac"])
                self._abort_if_unique_id_configured(updates={CONF_HOST: host})
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data={
                        CONF_HOST: host,
                        CONF_MAC: info["mac"],
                        CONF_DEVTYPE: info["devtype"],
                        CONF_MANUFACTURER: info["manufacturer"],
                        CONF_MODEL: info["model"],
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_NAME, default="BG Socket"): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

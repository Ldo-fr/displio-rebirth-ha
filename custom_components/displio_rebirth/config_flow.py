"""Config flow for Displio Rebirth integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import DisplioClient, DisplioConnectionError, DisplioResponseError
from .const import CONF_SCAN_INTERVAL, DEFAULT_PORT, DEFAULT_SCAN_INTERVAL, DOMAIN


class DisplioConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Displio Rebirth."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle the initial configuration step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = int(user_input.get(CONF_PORT, DEFAULT_PORT))
            session = async_get_clientsession(self.hass)
            client = DisplioClient(session, host, port)

            try:
                status = await client.get_status()
            except DisplioConnectionError:
                errors["base"] = "cannot_connect"
            except DisplioResponseError:
                errors["base"] = "invalid_device"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                mac = str(status.get("mac", "")).lower()
                unique_id = mac if mac else f"{host}:{port}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured(updates={CONF_HOST: host, CONF_PORT: port})

                title = f"Displio ({host})"
                return self.async_create_entry(
                    title=title,
                    data={CONF_HOST: host, CONF_PORT: port},
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_PORT, default=DEFAULT_PORT): vol.All(
                    vol.Coerce(int), vol.Range(min=1, max=65535)
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> DisplioOptionsFlow:
        """Return the options flow handler."""
        return DisplioOptionsFlow(config_entry)


class DisplioOptionsFlow(config_entries.OptionsFlow):
    """Handle options for Displio Rebirth."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Manage polling interval options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self._config_entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        schema = vol.Schema(
            {
                vol.Optional(CONF_SCAN_INTERVAL, default=current): vol.All(
                    vol.Coerce(int), vol.Range(min=5, max=3600)
                ),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)

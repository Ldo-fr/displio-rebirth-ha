"""The Displio Rebirth Home Assistant integration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv, device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import DisplioClient, DisplioError
from .const import (
    CONF_SCAN_INTERVAL,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    SERVICE_BEEP,
    SERVICE_DISPLAY_IMAGE,
    SERVICE_DISPLAY_TEXT,
)
from .coordinator import DisplioCoordinator
from .render import render_image_bytes, render_text_card

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
]

SCHEMA_DISPLAY_TEXT = vol.Schema(
    {
        vol.Optional("device_id"): cv.string,
        vol.Optional("title", default=""): cv.string,
        vol.Optional("body", default=""): cv.string,
        vol.Optional("footer", default=""): cv.string,
        vol.Optional("full_refresh", default=False): cv.boolean,
        vol.Optional("invert", default=False): cv.boolean,
        vol.Optional("beep", default=False): cv.boolean,
    }
)

SCHEMA_DISPLAY_IMAGE = vol.Schema(
    {
        vol.Optional("device_id"): cv.string,
        vol.Required("path"): cv.string,
        vol.Optional("full_refresh", default=True): cv.boolean,
        vol.Optional("dither", default=True): cv.boolean,
        vol.Optional("invert", default=False): cv.boolean,
    }
)

SCHEMA_BEEP = vol.Schema(
    {
        vol.Optional("device_id"): cv.string,
        vol.Optional("freq", default=2400): vol.All(vol.Coerce(int), vol.Range(min=100, max=10000)),
        vol.Optional("ms", default=80): vol.All(vol.Coerce(int), vol.Range(min=1, max=2000)),
    }
)


def _resolve_coordinators(
    hass: HomeAssistant,
    device_id: str | None,
) -> list[DisplioCoordinator]:
    """Resolve target Displio coordinator(s) from an optional HA device_id."""
    entries: dict[str, DisplioCoordinator] = hass.data.get(DOMAIN, {})
    if not entries:
        raise HomeAssistantError("No Displio Rebirth devices are configured")

    if not device_id:
        return [next(iter(entries.values()))]

    dev_reg = dr.async_get(hass)
    device = dev_reg.async_get(device_id)
    if device is None:
        raise HomeAssistantError(f"Unknown device_id: {device_id}")

    for entry_id in device.config_entries:
        if entry_id in entries:
            return [entries[entry_id]]

    raise HomeAssistantError(f"Device {device_id} does not belong to {DOMAIN}")


def _register_services(hass: HomeAssistant) -> None:
    """Register Displio Rebirth domain services once."""
    if hass.services.has_service(DOMAIN, SERVICE_DISPLAY_TEXT):
        return

    async def handle_display_text(call: ServiceCall) -> None:
        coords = _resolve_coordinators(hass, call.data.get("device_id"))
        fb = await hass.async_add_executor_job(
            render_text_card,
            call.data["title"],
            call.data["body"],
            call.data["footer"],
            call.data["invert"],
        )
        for coord in coords:
            try:
                await coord.client.post_display(fb, full_refresh=call.data["full_refresh"])
                if call.data["beep"]:
                    await coord.client.post_beep()
            except DisplioError as err:
                raise HomeAssistantError(str(err)) from err

    async def handle_display_image(call: ServiceCall) -> None:
        coords = _resolve_coordinators(hass, call.data.get("device_id"))
        source: str = call.data["path"].strip()

        if source.startswith(("http://", "https://")):
            session = async_get_clientsession(hass)
            try:
                async with session.get(source, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status != 200:
                        raise HomeAssistantError(f"Failed to download image: HTTP {resp.status}")
                    raw_img = await resp.read()
            except aiohttp.ClientError as err:
                raise HomeAssistantError(f"Failed to download image: {err}") from err
        else:
            if not hass.config.is_allowed_path(source):
                raise HomeAssistantError(
                    f"Path not allowed by Home Assistant allowlist_external_dirs: {source}"
                )
            p = Path(source)
            if not p.is_file():
                raise HomeAssistantError(f"Image file not found: {source}")
            raw_img = await hass.async_add_executor_job(p.read_bytes)

        fb = await hass.async_add_executor_job(
            render_image_bytes,
            raw_img,
            call.data["dither"],
            call.data["invert"],
        )
        for coord in coords:
            try:
                await coord.client.post_display(fb, full_refresh=call.data["full_refresh"])
            except DisplioError as err:
                raise HomeAssistantError(str(err)) from err

    async def handle_beep(call: ServiceCall) -> None:
        coords = _resolve_coordinators(hass, call.data.get("device_id"))
        for coord in coords:
            try:
                await coord.client.post_beep(freq=call.data["freq"], ms=call.data["ms"])
            except DisplioError as err:
                raise HomeAssistantError(str(err)) from err

    hass.services.async_register(DOMAIN, SERVICE_DISPLAY_TEXT, handle_display_text, schema=SCHEMA_DISPLAY_TEXT)
    hass.services.async_register(DOMAIN, SERVICE_DISPLAY_IMAGE, handle_display_image, schema=SCHEMA_DISPLAY_IMAGE)
    hass.services.async_register(DOMAIN, SERVICE_BEEP, handle_beep, schema=SCHEMA_BEEP)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Displio Rebirth from a config entry."""
    session = async_get_clientsession(hass)
    client = DisplioClient(
        session=session,
        host=entry.data[CONF_HOST],
        port=entry.data.get(CONF_PORT, DEFAULT_PORT),
    )
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    coordinator = DisplioCoordinator(hass, client, scan_interval=scan_interval)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    _register_services(hass)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Displio Rebirth config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not hass.data[DOMAIN]:
            for srv in (SERVICE_DISPLAY_TEXT, SERVICE_DISPLAY_IMAGE, SERVICE_BEEP):
                hass.services.async_remove(DOMAIN, srv)
    return unload_ok


def build_device_info(entry: ConfigEntry, data: dict[str, Any] | None) -> dr.DeviceInfo:
    """Build Home Assistant DeviceInfo for a Displio V1.0."""
    mac = str((data or {}).get("mac", "")).lower()
    fw = str((data or {}).get("fw", "1.0"))
    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, DEFAULT_PORT)

    connections = {(dr.CONNECTION_NETWORK_MAC, mac)} if mac else set()
    return dr.DeviceInfo(
        identifiers={(DOMAIN, mac or entry.entry_id)},
        connections=connections,
        name=entry.title,
        manufacturer="Displio (displio-rebirth)",
        model="Displio V1.0",
        sw_version=fw,
        configuration_url=f"http://{host}:{port}/",
    )

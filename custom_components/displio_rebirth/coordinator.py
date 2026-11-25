"""DataUpdateCoordinator for Displio Rebirth."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import DisplioClient, DisplioError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN, ORIENTATION_MAP
from .render import render_grid_card, render_text_card

_LOGGER = logging.getLogger(__name__)


class DisplioCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator polling GET /status on a Displio V1.0 device."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: DisplioClient,
        scan_interval: int = DEFAULT_SCAN_INTERVAL,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{client.host}",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.client = client
        self.last_auto_card: tuple[str, dict[str, Any]] | None = None
        self._last_orient: int | None = None

    async def _async_update_data(self) -> dict[str, Any]:
        """Poll sensor telemetry from the Displio HTTP API."""
        try:
            data = await self.client.get_status()
        except DisplioError as err:
            raise UpdateFailed(str(err)) from err

        new_orient = data.get("orientation")
        if (
            isinstance(new_orient, int)
            and self._last_orient is not None
            and new_orient != self._last_orient
            and self.last_auto_card is not None
        ):
            self.hass.async_create_task(self._async_rerender_for_orientation(new_orient))

        if isinstance(new_orient, int):
            self._last_orient = new_orient
        return data

    async def _async_rerender_for_orientation(self, orient_code: int) -> None:
        """Automatically re-render the last 'auto' card when the Displio is rotated."""
        if self.last_auto_card is None:
            return
        kind, params = self.last_auto_card
        orient_name = ORIENTATION_MAP.get(orient_code, "landscape_right")
        _LOGGER.debug(
            "Displio %s rotated to %s -> auto re-rendering %s card",
            self.client.host,
            orient_name,
            kind,
        )
        try:
            if kind == "grid":
                fb = await self.hass.async_add_executor_job(
                    render_grid_card,
                    params["tiles"],
                    orient_name,
                )
            else:
                fb = await self.hass.async_add_executor_job(
                    lambda: render_text_card(
                        params["title"],
                        params["body"],
                        params["footer"],
                        params["invert"],
                        icon=params["icon"],
                        subtitle=params["subtitle"],
                        layout=params["layout"],
                        orientation=orient_name,
                        details=params.get("details"),
                    )
                )
            await self.client.post_display(fb, full_refresh=False)
        except DisplioError as err:
            _LOGGER.warning("Failed to auto re-render after rotation: %s", err)

"""DataUpdateCoordinator for Displio Rebirth."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import DisplioClient, DisplioError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

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

    async def _async_update_data(self) -> dict[str, Any]:
        """Poll sensor telemetry from the Displio HTTP API."""
        try:
            return await self.client.get_status()
        except DisplioError as err:
            raise UpdateFailed(str(err)) from err

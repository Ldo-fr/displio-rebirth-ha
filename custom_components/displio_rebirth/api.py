"""Async HTTP client for the Displio Rebirth local REST API."""

from __future__ import annotations

import asyncio
from typing import Any

import aiohttp

from .const import DEFAULT_PORT, DEFAULT_TIMEOUT, EPD_FB_SIZE


class DisplioError(Exception):
    """Base exception for Displio Rebirth API errors."""


class DisplioConnectionError(DisplioError):
    """Raised when the Displio cannot be reached."""


class DisplioResponseError(DisplioError):
    """Raised when the Displio returns an unexpected response."""


class DisplioClient:
    """Async client communicating with a Displio V1.0 over local HTTP."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        host: str,
        port: int = DEFAULT_PORT,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        self._session = session
        self.host = host
        self.port = port
        self._base_url = f"http://{host}:{port}"
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        # CC3000 HTTP server handles one TCP client at a time
        self._lock = asyncio.Lock()

    async def get_status(self) -> dict[str, Any]:
        """Fetch live sensor telemetry and device metadata from GET /status."""
        url = f"{self._base_url}/status"
        headers = {"Connection": "close"}
        last_err: Exception | None = None

        async with self._lock:
            for attempt in range(2):
                try:
                    async with self._session.get(
                        url, headers=headers, timeout=self._timeout
                    ) as resp:
                        if resp.status != 200:
                            raise DisplioResponseError(
                                f"GET /status returned HTTP {resp.status}"
                            )
                        data = await resp.json(content_type=None)
                        break
                except (TimeoutError, aiohttp.ClientError) as err:
                    last_err = err
                    if attempt == 0:
                        await asyncio.sleep(0.5)
                        continue
                    raise DisplioConnectionError(
                        f"Error connecting to {url}: {last_err}"
                    ) from last_err
                except ValueError as err:
                    raise DisplioResponseError(
                        f"Invalid JSON from {url}: {err}"
                    ) from err

        if not isinstance(data, dict) or data.get("device") != "displio-rebirth":
            raise DisplioResponseError(
                "Target device is not a Displio Rebirth firmware"
            )
        return data

    async def post_display(
        self, framebuffer: bytes, full_refresh: bool = False
    ) -> None:
        """Push a 5,808-byte 1-bpp monochrome framebuffer to POST /display."""
        if len(framebuffer) != EPD_FB_SIZE:
            raise ValueError(
                f"Framebuffer must be exactly {EPD_FB_SIZE} bytes, got {len(framebuffer)}"
            )

        suffix = "?full=1" if full_refresh else ""
        url = f"{self._base_url}/display{suffix}"
        headers = {
            "Content-Type": "application/octet-stream",
            "Connection": "close",
        }
        async with self._lock:
            try:
                async with self._session.post(
                    url,
                    data=framebuffer,
                    headers=headers,
                    timeout=self._timeout,
                ) as resp:
                    if resp.status != 200:
                        raise DisplioResponseError(
                            f"POST /display returned HTTP {resp.status}"
                        )
                    await resp.read()
            except (TimeoutError, aiohttp.ClientError) as err:
                raise DisplioConnectionError(
                    f"Error posting display to {url}: {err}"
                ) from err

    async def post_beep(self, freq: int = 2400, ms: int = 80) -> None:
        """Trigger the onboard piezo buzzer via POST /beep."""
        freq = max(100, min(10000, int(freq)))
        ms = max(1, min(2000, int(ms)))
        url = f"{self._base_url}/beep?freq={freq}&ms={ms}"
        headers = {"Connection": "close"}
        async with self._lock:
            try:
                async with self._session.post(
                    url, headers=headers, timeout=self._timeout
                ) as resp:
                    if resp.status != 200:
                        raise DisplioResponseError(
                            f"POST /beep returned HTTP {resp.status}"
                        )
                    await resp.read()
            except (TimeoutError, aiohttp.ClientError) as err:
                raise DisplioConnectionError(
                    f"Error triggering beep at {url}: {err}"
                ) from err

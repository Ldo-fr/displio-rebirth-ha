"""Button platform for Displio Rebirth."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import build_device_info
from .api import DisplioError
from .const import DOMAIN
from .coordinator import DisplioCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Displio Rebirth button entities."""
    coordinator: DisplioCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([DisplioBeepButton(coordinator, entry)])


class DisplioBeepButton(CoordinatorEntity[DisplioCoordinator], ButtonEntity):
    """Button entity to trigger a short piezo beep on the Displio."""

    _attr_has_entity_name = True
    _attr_translation_key = "beep"
    _attr_icon = "mdi:volume-high"

    def __init__(self, coordinator: DisplioCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.unique_id or entry.entry_id}_beep"
        self._attr_device_info = build_device_info(entry, coordinator.data)

    async def async_press(self) -> None:
        """Trigger the piezo buzzer."""
        try:
            await self.coordinator.client.post_beep(freq=2400, ms=80)
        except DisplioError as err:
            raise HomeAssistantError(str(err)) from err

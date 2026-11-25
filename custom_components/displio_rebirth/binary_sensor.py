"""Binary sensor platform for Displio Rebirth."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import build_device_info
from .const import DOMAIN
from .coordinator import DisplioCoordinator


@dataclass(frozen=True, kw_only=True)
class DisplioBinarySensorDescription(BinarySensorEntityDescription):
    """Describes a Displio Rebirth binary sensor."""

    is_on_fn: Callable[[dict[str, Any]], bool | None]


BINARY_SENSORS: tuple[DisplioBinarySensorDescription, ...] = (
    DisplioBinarySensorDescription(
        key="usb_power",
        translation_key="usb_power",
        device_class=BinarySensorDeviceClass.PLUG,
        entity_category=EntityCategory.DIAGNOSTIC,
        is_on_fn=lambda d: bool(d["vbus"]) if "vbus" in d else None,
    ),
    DisplioBinarySensorDescription(
        key="button",
        translation_key="button",
        icon="mdi:gesture-tap-button",
        is_on_fn=lambda d: bool(d["button"]) if "button" in d else None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Displio Rebirth binary sensors."""
    coordinator: DisplioCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        DisplioBinarySensor(coordinator, entry, desc) for desc in BINARY_SENSORS
    )


class DisplioBinarySensor(CoordinatorEntity[DisplioCoordinator], BinarySensorEntity):
    """Representation of a Displio Rebirth binary sensor."""

    entity_description: DisplioBinarySensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DisplioCoordinator,
        entry: ConfigEntry,
        description: DisplioBinarySensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.unique_id or entry.entry_id}_{description.key}"
        self._attr_device_info = build_device_info(entry, coordinator.data)

    @property
    def is_on(self) -> bool | None:
        if not self.coordinator.data:
            return None
        return self.entity_description.is_on_fn(self.coordinator.data)

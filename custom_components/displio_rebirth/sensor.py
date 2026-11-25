"""Sensor platform for Displio Rebirth."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfElectricPotential,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import build_device_info
from .const import DOMAIN, ORIENTATION_MAP
from .coordinator import DisplioCoordinator


@dataclass(frozen=True, kw_only=True)
class DisplioSensorDescription(SensorEntityDescription):
    """Describes a Displio Rebirth sensor."""

    value_fn: Callable[[dict[str, Any]], Any]


SENSORS: tuple[DisplioSensorDescription, ...] = (
    DisplioSensorDescription(
        key="temperature",
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
        value_fn=lambda d: d.get("temp_c"),
    ),
    DisplioSensorDescription(
        key="humidity",
        translation_key="humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=1,
        value_fn=lambda d: d.get("humidity"),
    ),
    DisplioSensorDescription(
        key="orientation",
        translation_key="orientation",
        device_class=SensorDeviceClass.ENUM,
        options=list(ORIENTATION_MAP.values()),
        icon="mdi:screen-rotation",
        value_fn=lambda d: ORIENTATION_MAP.get(d.get("orientation")),
    ),
    DisplioSensorDescription(
        key="battery_adc",
        translation_key="battery_adc",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.get("vbat_adc_mv"),
    ),
    DisplioSensorDescription(
        key="vdda",
        translation_key="vdda",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda d: d.get("vdda_mv"),
    ),
    DisplioSensorDescription(
        key="uptime",
        translation_key="uptime",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: int(d["uptime_ms"]) // 1000 if "uptime_ms" in d else None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Displio Rebirth sensors."""
    coordinator: DisplioCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(DisplioSensor(coordinator, entry, desc) for desc in SENSORS)


class DisplioSensor(CoordinatorEntity[DisplioCoordinator], SensorEntity):
    """Representation of a Displio Rebirth sensor."""

    entity_description: DisplioSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DisplioCoordinator,
        entry: ConfigEntry,
        description: DisplioSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.unique_id or entry.entry_id}_{description.key}"
        self._attr_device_info = build_device_info(entry, coordinator.data)

    @property
    def native_value(self) -> Any:
        if not self.coordinator.data:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

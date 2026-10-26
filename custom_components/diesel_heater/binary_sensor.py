"""Heater on/off style sensors."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory

from . import HeaterEntity
from .const import DOMAIN


@dataclass(frozen=True, kw_only=True)
class HeaterBinaryDescription(BinarySensorEntityDescription):
    value_fn: Callable[[dict], bool]


BINARY_SENSORS: tuple[HeaterBinaryDescription, ...] = (
    HeaterBinaryDescription(
        key="glow_on", name="Glow plug", icon="mdi:flash",
        value_fn=lambda d: bool(d.get("glow")),
    ),
    HeaterBinaryDescription(
        key="fan_on", name="Fan", icon="mdi:fan",
        value_fn=lambda d: (d.get("fanOutput") or 0) > 0,
    ),
    HeaterBinaryDescription(
        key="pump_on", name="Fuel pump", icon="mdi:gas-station",
        value_fn=lambda d: bool(d.get("pumpOn")),
    ),
    HeaterBinaryDescription(
        key="schedule_active", name="Schedule active", icon="mdi:calendar-clock",
        value_fn=lambda d: bool(d.get("scheduleActive")),
    ),
    HeaterBinaryDescription(
        key="fault", name="Fault", device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda d: d.get("state") == "Fault",
    ),
    HeaterBinaryDescription(
        key="sta_connected", name="Wi-Fi connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: bool(d.get("staConnected")),
    ),
)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(HeaterBinarySensor(coordinator, d) for d in BINARY_SENSORS)


class HeaterBinarySensor(HeaterEntity, BinarySensorEntity):
    entity_description: HeaterBinaryDescription

    def __init__(self, coordinator, description: HeaterBinaryDescription) -> None:
        super().__init__(coordinator, description.key, description.name)
        self.entity_description = description

    @property
    def is_on(self) -> bool:
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self):
        if self.entity_description.key == "fault":
            return {"message": self.coordinator.data.get("fault") or None}
        if self.entity_description.key == "schedule_active":
            return {"schedules_enabled": self.coordinator.data.get("schedulesEnabled")}
        return None

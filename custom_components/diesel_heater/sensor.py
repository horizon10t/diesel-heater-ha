"""Heater sensors."""
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
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfFrequency,
    UnitOfTemperature,
    UnitOfTime,
)

from . import HeaterEntity
from .const import DOMAIN

STATES = ["Off", "Preheating", "Igniting", "Running", "Cooling", "Priming", "Fault"]


def _seconds(field: str) -> Callable[[dict], Any]:
    """Convert a millisecond field to whole seconds."""

    def convert(data: dict) -> Any:
        value = data.get(field)
        return None if value is None else round(value / 1000)

    return convert


def _last_run(data: dict) -> Any:
    runs = data.get("runtimeRecentRuns") or []
    return runs[-1] if runs else None


def _text(field: str) -> Callable[[dict], Any]:
    return lambda data: data.get(field) or None


@dataclass(frozen=True, kw_only=True)
class HeaterSensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict], Any]
    attrs_fn: Callable[[dict], dict] | None = None


DIAG = EntityCategory.DIAGNOSTIC

SENSORS: tuple[HeaterSensorDescription, ...] = (
    HeaterSensorDescription(
        key="core_temperature", name="Core temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("coreTemperature"),
    ),
    HeaterSensorDescription(
        key="cabin_temperature", name="Cabin temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("temperature"),
    ),
    HeaterSensorDescription(
        key="voltage", name="Voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("batteryVoltage"),
    ),
    HeaterSensorDescription(
        key="current", name="Current",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("batteryCurrent"),
    ),
    # Output states (percentages; on/off versions are binary sensors)
    HeaterSensorDescription(
        key="glow_output", name="Glow plug output", icon="mdi:flash",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("glowOutput"),
    ),
    HeaterSensorDescription(
        key="fan_output", name="Fan output", icon="mdi:fan",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("fanOutput"),
    ),
    HeaterSensorDescription(
        key="pump_rate", name="Fuel pump rate", icon="mdi:gas-station",
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.get("pumpHz"),
    ),
    # Runtime
    HeaterSensorDescription(
        key="last_run", name="Last run duration",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.MINUTES,
        value_fn=_last_run,
        attrs_fn=lambda d: {"recent_runs_seconds": d.get("runtimeRecentRuns") or []},
    ),
    HeaterSensorDescription(
        key="average_runtime", name="Average runtime",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.MINUTES,
        value_fn=_seconds("runtimeAverageMs"),
        attrs_fn=lambda d: {"completed_runs": d.get("runtimeCompletedRuns")},
    ),
    HeaterSensorDescription(
        key="total_runtime", name="Total runtime",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=_seconds("runtimeTotalMs"),
    ),
    # Network and firmware
    HeaterSensorDescription(
        key="ip_address", name="IP address", icon="mdi:ip-network",
        entity_category=DIAG, value_fn=_text("staIp"),
    ),
    HeaterSensorDescription(
        key="wifi_network", name="Active Wi-Fi network", icon="mdi:wifi",
        entity_category=DIAG, value_fn=_text("connectedSsid"),
    ),
    HeaterSensorDescription(
        key="sta_status", name="Station status", icon="mdi:wifi-check",
        entity_category=DIAG, value_fn=_text("staStatus"),
    ),
    HeaterSensorDescription(
        key="ap_status", name="Access point status", icon="mdi:access-point",
        entity_category=DIAG, value_fn=_text("apStatus"),
    ),
    HeaterSensorDescription(
        key="firmware_version", name="Installed version", icon="mdi:chip",
        entity_category=DIAG, value_fn=_text("firmwareVersion"),
    ),
)


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = [HeaterStatusSensor(coordinator)]
    entities += [HeaterSensor(coordinator, description) for description in SENSORS]
    async_add_entities(entities)


class HeaterStatusSensor(HeaterEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = STATES
    _attr_icon = "mdi:fire"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "status", "Status")

    @property
    def native_value(self):
        value = self.coordinator.data.get("state")
        return value if value in STATES else None

    @property
    def extra_state_attributes(self):
        d = self.coordinator.data
        return {
            "fault": d.get("fault") or None,
            "profile": d.get("activeProfile"),
            "thermal_derating": d.get("thermalDerating"),
        }


class HeaterSensor(HeaterEntity, SensorEntity):
    entity_description: HeaterSensorDescription

    def __init__(self, coordinator, description: HeaterSensorDescription) -> None:
        super().__init__(coordinator, description.key, description.name)
        self.entity_description = description

    @property
    def native_value(self):
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self):
        if self.entity_description.attrs_fn:
            return self.entity_description.attrs_fn(self.coordinator.data)
        return None

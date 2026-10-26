"""Heater sensors."""
from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import UnitOfElectricCurrent, UnitOfElectricPotential, UnitOfTemperature

from . import HeaterEntity
from .const import DOMAIN

STATES = ["Off", "Preheating", "Igniting", "Running", "Cooling", "Priming", "Fault"]

NUMERIC = [
    ("core_temperature", "Core temperature", "coreTemperature", SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS),
    ("cabin_temperature", "Cabin temperature", "temperature", SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS),
    ("voltage", "Voltage", "batteryVoltage", SensorDeviceClass.VOLTAGE, UnitOfElectricPotential.VOLT),
    ("current", "Current", "batteryCurrent", SensorDeviceClass.CURRENT, UnitOfElectricCurrent.AMPERE),
]


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [HeaterStatusSensor(coordinator)]
    entities += [HeaterNumericSensor(coordinator, *spec) for spec in NUMERIC]
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
            "glow": d.get("glow"),
            "fan_output": d.get("fanOutput"),
            "pump_hz": d.get("pumpHz"),
            "thermal_derating": d.get("thermalDerating"),
        }


class HeaterNumericSensor(HeaterEntity, SensorEntity):
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, key, name, field, device_class, unit) -> None:
        super().__init__(coordinator, key, name)
        self._field = field
        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = unit

    @property
    def native_value(self):
        return self.coordinator.data.get(self._field)

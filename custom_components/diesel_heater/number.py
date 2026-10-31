"""Power level, target temperature, fan speed and fuel pump rate."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import PERCENTAGE, UnitOfFrequency, UnitOfTemperature
from homeassistant.exceptions import HomeAssistantError

from . import HeaterEntity
from .api import HeaterError
from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    c = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        HeaterNumber(c, "power_level", "Power level", "powerLevel", "level", 1, 10, None, "mdi:speedometer"),
        HeaterNumber(c, "target_temperature", "Target temperature", "target", "target", 5, 35,
                     UnitOfTemperature.CELSIUS, "mdi:thermostat"),
        HeaterFanSpeed(c),
        HeaterPumpRate(c),
    ])


class HeaterNumber(HeaterEntity, NumberEntity):
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER

    def __init__(self, coordinator, key, name, field, param, lo, hi, unit, icon) -> None:
        super().__init__(coordinator, key, name)
        self._field, self._param = field, param
        self._attr_native_min_value, self._attr_native_max_value = lo, hi
        self._attr_native_unit_of_measurement = unit
        self._attr_icon = icon

    @property
    def native_value(self):
        return self.coordinator.data.get(self._field)

    async def async_set_native_value(self, value: float) -> None:
        self.coordinator.async_set_updated_data(
            await self.coordinator.client.set_mode(**{self._param: int(value)})
        )


class HeaterTuneNumber(HeaterEntity, NumberEntity):
    """Fan speed or fuel pump rate for the current power level.

    Same as the live tuning in the controller's web interface: Power mode only,
    not saved, and dropped when the power level or mode changes or the heater
    stops.
    """

    _attr_mode = NumberMode.SLIDER
    _field = ""
    _param = ""

    @property
    def native_value(self):
        return self.coordinator.data.get(self._field)

    async def async_set_native_value(self, value: float) -> None:
        try:
            data = await self.coordinator.client.tune(**{self._param: self._format(value)})
        except HeaterError as err:
            raise HomeAssistantError(str(err)) from err
        self.coordinator.async_set_updated_data(data)

    @staticmethod
    def _format(value: float):
        return value


class HeaterFanSpeed(HeaterTuneNumber):
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_icon = "mdi:fan"
    _field = "powerFan"
    _param = "fan"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "fan_speed", "Fan speed")

    @property
    def native_min_value(self) -> float:
        return float(self.coordinator.data.get("minimumFan", 0))

    @property
    def native_max_value(self) -> float:
        return 100.0

    @staticmethod
    def _format(value: float):
        return int(round(value))


class HeaterPumpRate(HeaterTuneNumber):
    _attr_native_step = 0.1
    _attr_native_unit_of_measurement = UnitOfFrequency.HERTZ
    _attr_icon = "mdi:gas-station"
    _field = "powerPumpHz"
    _param = "pumpHz"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "fuel_pump_rate", "Fuel pump rate")

    @property
    def native_min_value(self) -> float:
        return 1.5

    @property
    def native_max_value(self) -> float:
        return float(self.coordinator.data.get("maximumPumpHz", 8.0))

    @staticmethod
    def _format(value: float):
        return round(value, 1)

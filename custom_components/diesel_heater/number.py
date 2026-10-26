"""Power level and target temperature."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import UnitOfTemperature

from . import HeaterEntity
from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    c = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        HeaterNumber(c, "power_level", "Power level", "powerLevel", "level", 1, 10, None, "mdi:speedometer"),
        HeaterNumber(c, "target_temperature", "Target temperature", "target", "target", 5, 35,
                     UnitOfTemperature.CELSIUS, "mdi:thermostat"),
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

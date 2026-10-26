"""Heater on/off."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity

from . import HeaterEntity
from .const import DOMAIN

ACTIVE = {"Preheating", "Igniting", "Running", "Priming"}


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([HeaterPowerSwitch(hass.data[DOMAIN][entry.entry_id])])


class HeaterPowerSwitch(HeaterEntity, SwitchEntity):
    _attr_icon = "mdi:power"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "power", "Power")

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.get("state") in ACTIVE

    async def async_turn_on(self, **kwargs) -> None:
        self.coordinator.async_set_updated_data(await self.coordinator.client.set_power(True))

    async def async_turn_off(self, **kwargs) -> None:
        self.coordinator.async_set_updated_data(await self.coordinator.client.set_power(False))

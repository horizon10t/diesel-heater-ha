"""Emergency stop button."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity

from . import HeaterEntity
from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([HeaterEmergencyStop(hass.data[DOMAIN][entry.entry_id])])


class HeaterEmergencyStop(HeaterEntity, ButtonEntity):
    _attr_icon = "mdi:alert-octagon"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "emergency_stop", "Emergency stop")

    async def async_press(self) -> None:
        self.coordinator.async_set_updated_data(
            await self.coordinator.client.emergency_stop()
        )

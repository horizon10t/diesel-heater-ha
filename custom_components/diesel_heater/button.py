"""Emergency stop and clear fault buttons."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity

from . import HeaterEntity
from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([HeaterEmergencyStop(coordinator), HeaterClearFault(coordinator)])


class HeaterEmergencyStop(HeaterEntity, ButtonEntity):
    _attr_icon = "mdi:alert-octagon"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "emergency_stop", "Emergency stop")

    async def async_press(self) -> None:
        self.coordinator.async_set_updated_data(
            await self.coordinator.client.emergency_stop()
        )


class HeaterClearFault(HeaterEntity, ButtonEntity):
    """Same as the Clear button in the controller's web interface."""

    _attr_icon = "mdi:alert-remove"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "clear_fault", "Clear fault")

    async def async_press(self) -> None:
        self.coordinator.async_set_updated_data(
            await self.coordinator.client.clear_fault()
        )

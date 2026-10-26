"""Operating mode select."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity

from . import HeaterEntity
from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([HeaterModeSelect(hass.data[DOMAIN][entry.entry_id])])


class HeaterModeSelect(HeaterEntity, SelectEntity):
    _attr_options = ["Thermostat", "Power"]
    _attr_icon = "mdi:tune-variant"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "operating_mode", "Operating mode")

    @property
    def current_option(self):
        mode = self.coordinator.data.get("operatingMode")
        return mode.title() if mode else None

    async def async_select_option(self, option: str) -> None:
        self.coordinator.async_set_updated_data(
            await self.coordinator.client.set_mode(mode=option.lower())
        )

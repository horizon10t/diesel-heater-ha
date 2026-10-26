"""Diesel Heater Controller integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import HeaterAuthError, HeaterClient, HeaterError
from .const import CONF_API_KEY, DOMAIN, PLATFORMS, SCAN_INTERVAL_SECONDS

_LOGGER = logging.getLogger(__name__)


class HeaterCoordinator(DataUpdateCoordinator[dict]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: HeaterClient) -> None:
        super().__init__(
            hass, _LOGGER, name=DOMAIN, config_entry=entry,
            update_interval=timedelta(seconds=SCAN_INTERVAL_SECONDS),
        )
        self.client = client
        self.host = entry.data[CONF_HOST]

    async def _async_update_data(self) -> dict:
        try:
            return await self.client.status()
        except HeaterAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except HeaterError as err:
            raise UpdateFailed(str(err)) from err


class HeaterEntity(CoordinatorEntity[HeaterCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: HeaterCoordinator, key: str, name: str) -> None:
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = f"{coordinator.host}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.host)},
            name="Diesel Heater",
            manufacturer="deanfourie.me",
            model="ESP32-S3 Heater Controller",
            sw_version=coordinator.data.get("firmwareVersion") if coordinator.data else None,
            configuration_url=f"http://{coordinator.host}",
        )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    client = HeaterClient(
        async_get_clientsession(hass), entry.data[CONF_HOST], entry.data[CONF_API_KEY]
    )
    coordinator = HeaterCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return ok

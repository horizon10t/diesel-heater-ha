"""Diesel Heater Controller integration."""
from __future__ import annotations

import logging
from datetime import timedelta
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
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


CARD_URL = "/diesel_heater/diesel-heater-card.js"
CARD_VERSION = "1.2.1"  # bump with manifest.json so browsers reload the card


async def _register_card_resource(hass: HomeAssistant, url: str) -> bool:
    """Add (or update) the card as a dashboard resource, like doing it by hand.

    Only possible when dashboards are in storage mode; returns False otherwise.
    """
    try:
        from homeassistant.components.lovelace.const import LOVELACE_DATA

        resources = hass.data[LOVELACE_DATA].resources
    except (ImportError, KeyError, AttributeError):
        lovelace = hass.data.get("lovelace")
        resources = getattr(lovelace, "resources", None)
    if resources is None or not hasattr(resources, "async_create_item"):
        return False  # YAML mode or lovelace not available

    if not getattr(resources, "loaded", True):
        await resources.async_load()
        resources.loaded = True

    for item in resources.async_items():
        if item["url"].split("?")[0] == CARD_URL:
            if item["url"] != url:
                await resources.async_update_item(
                    item["id"], {"res_type": "module", "url": url}
                )
            return True
    await resources.async_create_item({"res_type": "module", "url": url})
    return True


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Serve the Lovelace card and make every dashboard load it."""
    card = Path(__file__).parent / "diesel-heater-card.js"
    await hass.http.async_register_static_paths(
        [StaticPathConfig(CARD_URL, str(card), False)]
    )
    url = f"{CARD_URL}?v={CARD_VERSION}"
    try:
        registered = await _register_card_resource(hass, url)
    except Exception:  # noqa: BLE001 - never let the card break the integration
        _LOGGER.exception("Could not register the Lovelace card resource")
        registered = False
    # Fallback for YAML-mode dashboards or if the resource could not be added.
    # The card guards against being loaded twice.
    if not registered:
        add_extra_js_url(hass, url)
    return True


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

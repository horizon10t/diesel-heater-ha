"""Config flow: host + WebUI login (and MFA code if enabled)."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME

from .api import (
    HeaterAuthError,
    HeaterError,
    MfaRequired,
    UnexpectedResponse,
    fetch_api_key,
)
from .const import CONF_API_KEY, DOMAIN

_LOGGER = logging.getLogger(__name__)


class DieselHeaterConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._host = ""
        self._username = ""
        self._password = ""

    async def _finish(self, api_key: str) -> ConfigFlowResult:
        await self.async_set_unique_id(self._host.lower())
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=f"Diesel Heater ({self._host})",
            data={CONF_HOST: self._host, CONF_API_KEY: api_key},
        )

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            self._host = user_input[CONF_HOST].strip().removeprefix("http://").rstrip("/")
            self._username = user_input[CONF_USERNAME]
            self._password = user_input[CONF_PASSWORD]
            try:
                key = await fetch_api_key(self._host, self._username, self._password)
            except MfaRequired:
                return await self.async_step_mfa()
            except HeaterAuthError:
                errors["base"] = "invalid_auth"
            except UnexpectedResponse as err:
                _LOGGER.warning("Diesel heater setup: %s", err)
                errors["base"] = "unexpected_response"
            except HeaterError as err:
                _LOGGER.warning("Diesel heater setup could not connect: %s", err)
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001 - show a form error, never crash the flow
                _LOGGER.exception("Unexpected error during Diesel heater setup")
                errors["base"] = "unknown"
            else:
                return await self._finish(key)
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=self._host): str,
                    vol.Required(CONF_USERNAME, default=self._username): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

    async def async_step_mfa(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                key = await fetch_api_key(
                    self._host, self._username, self._password, user_input["code"].strip()
                )
            except (MfaRequired, HeaterAuthError):
                errors["base"] = "invalid_code"
            except UnexpectedResponse as err:
                _LOGGER.warning("Diesel heater setup: %s", err)
                errors["base"] = "unexpected_response"
            except HeaterError as err:
                _LOGGER.warning("Diesel heater setup could not connect: %s", err)
                errors["base"] = "cannot_connect"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error during Diesel heater setup")
                errors["base"] = "unknown"
            else:
                return await self._finish(key)
        return self.async_show_form(
            step_id="mfa",
            data_schema=vol.Schema({vol.Required("code"): str}),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: dict[str, Any]) -> ConfigFlowResult:
        self._host = entry_data[CONF_HOST]
        return await self.async_step_user()

"""Small client for the heater controller's /api/ha endpoints."""
from __future__ import annotations

import asyncio

import aiohttp

TIMEOUT = aiohttp.ClientTimeout(total=8)


class HeaterError(Exception):
    """Controller returned an error or could not be reached."""


class HeaterAuthError(HeaterError):
    """The API key or login was rejected."""


class HeaterClient:
    """Talks to the controller using the X-API-Key header."""

    def __init__(self, session: aiohttp.ClientSession, host: str, api_key: str) -> None:
        self._session = session
        self._base = f"http://{host}"
        self._headers = {"X-API-Key": api_key}

    async def _request(self, method: str, path: str, data: dict | None = None) -> dict:
        try:
            async with self._session.request(
                method, self._base + path, headers=self._headers, data=data, timeout=TIMEOUT
            ) as resp:
                if resp.status == 401:
                    raise HeaterAuthError("Invalid API key")
                body = await resp.json(content_type=None)
                if resp.status >= 400:
                    raise HeaterError(body.get("error", f"HTTP {resp.status}"))
                return body
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise HeaterError(str(err)) from err

    async def status(self) -> dict:
        return await self._request("GET", "/api/ha/status")

    async def set_mode(self, **fields) -> dict:
        return await self._request("POST", "/api/ha/mode", {k: str(v) for k, v in fields.items()})

    async def set_power(self, on: bool) -> dict:
        return await self._request("POST", "/api/ha/power", {"on": "true" if on else "false"})




async def fetch_api_key(host: str, username: str, password: str, code: str | None = None) -> str:
    """Log in with a WebUI account and read the API key. The password is not kept.

    Returns the key, or raises HeaterAuthError / HeaterError. Raises
    MfaRequired when the account needs an authentication code.
    """
    base = f"http://{host}"
    jar = aiohttp.CookieJar(unsafe=True)  # the controller is addressed by IP
    async with aiohttp.ClientSession(cookie_jar=jar) as session:
        try:
            form = {"username": username, "password": password}
            if code:
                form["code"] = code
            async with session.post(base + "/api/auth/login", data=form, timeout=TIMEOUT) as resp:
                body = await resp.json(content_type=None)
                if resp.status in (401, 429):
                    raise HeaterAuthError(body.get("error", "Login failed"))
                if resp.status >= 400:
                    raise HeaterError(body.get("error", f"HTTP {resp.status}"))
                if body.get("mfaRequired"):
                    raise MfaRequired
            async with session.get(base + "/api/ha/key", timeout=TIMEOUT) as resp:
                if resp.status == 403:
                    raise HeaterAuthError("This user needs the Settings permission")
                if resp.status >= 400:
                    raise HeaterError(f"HTTP {resp.status}")
                key = (await resp.json(content_type=None)).get("key", "")
            try:
                await session.post(base + "/api/auth/logout", timeout=TIMEOUT)
            except (aiohttp.ClientError, asyncio.TimeoutError):
                pass
            if not key:
                raise HeaterError("Controller returned no API key")
            return key
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise HeaterError(str(err)) from err


class MfaRequired(Exception):
    """The account has MFA enabled and needs a code."""

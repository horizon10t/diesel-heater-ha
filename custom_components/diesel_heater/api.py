"""Small client for the heater controller's /api/ha endpoints."""
from __future__ import annotations

import asyncio

import aiohttp

TIMEOUT = aiohttp.ClientTimeout(total=8)


class HeaterError(Exception):
    """Controller returned an error or could not be reached."""


class HeaterAuthError(HeaterError):
    """The API key or login was rejected."""


class UnexpectedResponse(HeaterError):
    """The address answered, but not like a heater controller (no JSON)."""


async def _read_json(resp: aiohttp.ClientResponse) -> dict:
    """Decode a JSON object reply, or raise a clear error.

    The controller answers unknown paths with a redirect to its login page, so
    an old firmware or a wrong address ends up here as HTML rather than JSON.
    """
    try:
        data = await resp.json(content_type=None)
    except (ValueError, aiohttp.ContentTypeError) as err:
        raise UnexpectedResponse(
            f"Unexpected reply from {resp.url} (HTTP {resp.status}); "
            "check the address and that the controller has the latest firmware"
        ) from err
    if not isinstance(data, dict):
        raise UnexpectedResponse(f"Unexpected reply from {resp.url} (HTTP {resp.status})")
    return data


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
                body = await _read_json(resp)
                if resp.status >= 400:
                    raise HeaterError(body.get("error", f"HTTP {resp.status}"))
                return body
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise HeaterError(str(err)) from err

    async def status(self) -> dict:
        return await self._request("GET", "/api/ha/status")

    async def set_mode(self, **fields) -> dict:
        return await self._request("POST", "/api/ha/mode", {k: str(v) for k, v in fields.items()})

    async def emergency_stop(self) -> dict:
        return await self._request("POST", "/api/ha/estop")

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
                body = await _read_json(resp)
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
                key = (await _read_json(resp)).get("key", "")
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

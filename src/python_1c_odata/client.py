"""Shared HTTP session for one published 1C infobase."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import aiohttp

from python_1c_odata.errors import ODataError, error_from_response
from python_1c_odata.literals import parse_guid
from python_1c_odata.url import entity_path, infobase_root, key_path, query_string

_OK = {
    "GET": frozenset({200}),
    "POST": frozenset({200, 201}),
    "PATCH": frozenset({200}),
    "PUT": frozenset({200}),
    "DELETE": frozenset({200, 204}),
}


class Infobase:
    def __init__(
        self,
        server: str,
        infobase: str,
        username: str,
        password: str,
        *,
        timeout: float = 30,
        ssl: bool | aiohttp.Fingerprint | None = True,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        self.server = server
        self.infobase = infobase
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._ssl = ssl
        self._session = session
        self._owns_session = session is None
        self._headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": aiohttp.encode_basic_auth(username, password, encoding="utf-8"),
        }

    @property
    def root(self) -> str:
        return infobase_root(self.server, self.infobase)

    @property
    def session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            raise RuntimeError("HTTP session is not started")
        return self._session

    async def __aenter__(self) -> Infobase:
        await self._ensure_session()
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._owns_session and self._session is not None and not self._session.closed:
            await self._session.close()
            self._session = None

    def url(
        self,
        entity: str,
        *,
        key: str | Mapping[str, str] | None = None,
        action: str | None = None,
        **query: Any,
    ) -> str:
        if key is None:
            path = entity_path(self.root, entity)
        else:
            path = key_path(self.root, entity, self._normalize_key(key))
            if action:
                path = f"{path}/{action}"
        extra = query.pop("extra", None)
        return path + query_string(extra=extra, **query)

    async def get(self, entity: str, *, key: str | Mapping[str, str] | None = None, **query: Any) -> Any:
        timeout = query.pop("timeout", None)
        return await self.request("GET", self.url(entity, key=key, **query), timeout=timeout)

    async def post(
        self,
        entity: str,
        *,
        json: Any = None,
        key: str | Mapping[str, str] | None = None,
        action: str | None = None,
        extra: Mapping[str, str] | None = None,
        timeout: float | None = None,
    ) -> Any:
        return await self.request(
            "POST",
            self.url(entity, key=key, action=action, extra=extra),
            json_body=json,
            timeout=timeout,
        )

    async def patch(
        self,
        entity: str,
        *,
        key: str | Mapping[str, str],
        json: Any,
        timeout: float | None = None,
    ) -> Any:
        return await self.request("PATCH", self.url(entity, key=key), json_body=json, timeout=timeout)

    async def put(
        self,
        entity: str,
        *,
        key: str | Mapping[str, str],
        json: Any,
        timeout: float | None = None,
    ) -> Any:
        return await self.request("PUT", self.url(entity, key=key), json_body=json, timeout=timeout)

    async def delete(
        self,
        entity: str,
        *,
        key: str | Mapping[str, str],
        timeout: float | None = None,
    ) -> Any:
        return await self.request("DELETE", self.url(entity, key=key), timeout=timeout)

    async def request(
        self,
        method: str,
        url: str,
        *,
        json_body: Any = None,
        timeout: float | None = None,
        ok: set[int] | None = None,
    ) -> Any:
        await self._ensure_session()
        allowed = ok or _OK[method]
        kwargs: dict[str, Any] = {"headers": self._headers}
        if self._ssl is not True:
            kwargs["ssl"] = self._ssl
        if timeout is not None:
            kwargs["timeout"] = aiohttp.ClientTimeout(total=timeout)
        if json_body is not None:
            kwargs["json"] = json_body
        assert self._session is not None
        async with self._session.request(method, url, **kwargs) as response:
            text = await response.text()
            if response.status not in allowed:
                raise error_from_response(response.status, text)
            if not text:
                return None
            try:
                return json.loads(text)
            except ValueError as exc:
                raise ODataError(response.status, f"invalid JSON: {text[:200]}", body=text) from exc

    async def _ensure_session(self) -> None:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self._timeout)
            self._owns_session = True

    @staticmethod
    def _normalize_key(key: str | Mapping[str, str]) -> str | Mapping[str, str]:
        if isinstance(key, Mapping):
            return key
        return parse_guid(key)

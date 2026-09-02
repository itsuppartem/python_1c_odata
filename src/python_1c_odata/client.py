"""Shared HTTP session for one published 1C infobase."""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable, Mapping
from typing import Any
from urllib.parse import unquote

import aiohttp

from python_1c_odata.errors import ODataError, error_from_response
from python_1c_odata.literals import parse_guid
from python_1c_odata.url import entity_path, infobase_root, key_path, query_string

_LOG = logging.getLogger("python_1c_odata")

_OK = {
    "GET": frozenset({200}),
    "POST": frozenset({200, 201}),
    "PATCH": frozenset({200}),
    "PUT": frozenset({200}),
    "DELETE": frozenset({200, 204}),
}

DebugHook = bool | Callable[[str], object]


def _if_match_headers(if_match: str | None) -> dict[str, str] | None:
    if if_match is None:
        return None
    return {"If-Match": if_match}


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
        debug: DebugHook = False,
    ) -> None:
        self.server = server
        self.infobase = infobase
        self.debug = debug
        self.last_url: str | None = None
        self.last_status: int | None = None
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
        allowed_only = query.pop("allowed_only", False)
        inlinecount = query.pop("inlinecount", False)
        return path + query_string(
            extra=extra,
            allowed_only=bool(allowed_only),
            inlinecount=bool(inlinecount),
            **query,
        )

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
        if_match: str | None = None,
    ) -> Any:
        return await self.request(
            "PATCH",
            self.url(entity, key=key),
            json_body=json,
            timeout=timeout,
            headers=_if_match_headers(if_match),
        )

    async def put(
        self,
        entity: str,
        *,
        key: str | Mapping[str, str],
        json: Any,
        timeout: float | None = None,
        if_match: str | None = None,
    ) -> Any:
        return await self.request(
            "PUT",
            self.url(entity, key=key),
            json_body=json,
            timeout=timeout,
            headers=_if_match_headers(if_match),
        )

    async def delete(
        self,
        entity: str,
        *,
        key: str | Mapping[str, str],
        timeout: float | None = None,
        if_match: str | None = None,
    ) -> Any:
        return await self.request(
            "DELETE",
            self.url(entity, key=key),
            timeout=timeout,
            headers=_if_match_headers(if_match),
        )

    async def request(
        self,
        method: str,
        url: str,
        *,
        json_body: Any = None,
        timeout: float | None = None,
        ok: set[int] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Any:
        await self._ensure_session()
        allowed = ok or _OK[method]
        merged = dict(self._headers)
        if headers:
            merged.update(headers)
        kwargs: dict[str, Any] = {"headers": merged}
        if self._ssl is not True:
            kwargs["ssl"] = self._ssl
        if timeout is not None:
            kwargs["timeout"] = aiohttp.ClientTimeout(total=timeout)
        if json_body is not None:
            kwargs["json"] = json_body
        assert self._session is not None
        decoded = unquote(url)
        self.last_url = decoded
        started = time.perf_counter()
        async with self._session.request(method, url, **kwargs) as response:
            text = await response.text()
            elapsed_ms = (time.perf_counter() - started) * 1000
            self.last_status = response.status
            self._emit_debug(method, decoded, response.status, elapsed_ms)
            if response.status not in allowed:
                raise error_from_response(response.status, text)
            if not text:
                return None
            try:
                return json.loads(text)
            except ValueError as exc:
                raise ODataError(response.status, f"invalid JSON: {text[:200]}", body=text) from exc

    async def metadata(self, *, timeout: float | None = None) -> str:
        await self._ensure_session()
        url = f"{self.root}/$metadata"
        kwargs: dict[str, Any] = {"headers": {**self._headers, "Accept": "application/xml"}}
        if self._ssl is not True:
            kwargs["ssl"] = self._ssl
        if timeout is not None:
            kwargs["timeout"] = aiohttp.ClientTimeout(total=timeout)
        assert self._session is not None
        decoded = unquote(url)
        self.last_url = decoded
        started = time.perf_counter()
        async with self._session.request("GET", url, **kwargs) as response:
            text = await response.text()
            elapsed_ms = (time.perf_counter() - started) * 1000
            self.last_status = response.status
            self._emit_debug("GET", decoded, response.status, elapsed_ms)
            if response.status != 200:
                raise error_from_response(response.status, text)
            return text

    def _emit_debug(self, method: str, url: str, status: int, elapsed_ms: float) -> None:
        if not self.debug:
            return
        line = f"{method} {url} {status} {elapsed_ms:.1f}ms"
        if self.debug is True:
            _LOG.info(line)
        elif callable(self.debug):
            self.debug(line)

    async def _ensure_session(self) -> None:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self._timeout)
            self._owns_session = True

    @staticmethod
    def _normalize_key(key: str | Mapping[str, str]) -> str | Mapping[str, str]:
        if isinstance(key, Mapping):
            return key
        return parse_guid(key)

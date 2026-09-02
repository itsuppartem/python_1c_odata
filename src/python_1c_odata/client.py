"""Shared HTTP session for one published 1C infobase."""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Callable, Mapping
from typing import Any
from urllib.parse import unquote
from xml.etree import ElementTree

import aiohttp

from python_1c_odata.atom import (
    decode_atom,
    encode_entry,
    looks_like_atom,
    looks_like_xml_content_type,
)
from python_1c_odata.errors import ODataError, error_from_response
from python_1c_odata.literals import parse_guid
from python_1c_odata.metadata import EntityTypeInfo, MetadataModel, parse_metadata
from python_1c_odata.presentation import normalize_select
from python_1c_odata.url import entity_path, infobase_root, key_path, query_string

_LOG = logging.getLogger("python_1c_odata")

DATA_LOAD_MODE_HEADER = "1C_OData-DataLoadMode"

_OK = {
    "GET": frozenset({200}),
    "POST": frozenset({200, 201}),
    "PATCH": frozenset({200}),
    "PUT": frozenset({200}),
    "DELETE": frozenset({200, 204}),
}

_FORMATS = frozenset({"json", "atom", "auto"})
_ATOM_ACCEPT = "application/atom+xml,application/xml"
_JSON_ACCEPT = "application/json"
_ATOM_CONTENT = "application/atom+xml"
_JSON_CONTENT = "application/json"
_ATOM_VERSION = "3.0"

DebugHook = bool | Callable[[str], object]


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
        data_load_mode: bool = False,
        format: str = "json",
    ) -> None:
        if format not in _FORMATS:
            raise ValueError(f"format={format!r} must be 'json', 'atom', or 'auto'")
        self.server = server
        self.infobase = infobase
        self.debug = debug
        self.data_load_mode = data_load_mode
        self.format = format
        self.last_url: str | None = None
        self.last_status: int | None = None
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._ssl = ssl
        self._session = session
        self._owns_session = session is None
        self._entity_set_names: list[str] | None = None
        self._metadata_model: MetadataModel | None = None
        atom = format == "atom"
        self._headers = {
            "Accept": _ATOM_ACCEPT if atom else _JSON_ACCEPT,
            "Content-Type": _ATOM_CONTENT if atom else _JSON_CONTENT,
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
        presentations = query.pop("presentations", False)
        select = normalize_select(query.pop("select", None), presentations=bool(presentations))
        query.pop("odata_format", None)
        return path + self.odata_query_string(
            extra=extra,
            allowed_only=bool(allowed_only),
            inlinecount=bool(inlinecount),
            select=select,
            **query,
        )

    def odata_query_string(self, **kwargs: Any) -> str:
        """``url.query_string`` with this infobase's ``$format`` (json or atom)."""
        kwargs.pop("odata_format", None)
        return query_string(odata_format=self._query_format, **kwargs)

    @property
    def _query_format(self) -> str:
        return "atom" if self.format == "atom" else "json"

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
        data_load_mode: bool | None = None,
    ) -> Any:
        return await self.request(
            "POST",
            self.url(entity, key=key, action=action, extra=extra),
            json_body=json,
            timeout=timeout,
            headers=self._write_headers(data_load_mode=data_load_mode),
        )

    async def patch(
        self,
        entity: str,
        *,
        key: str | Mapping[str, str],
        json: Any,
        timeout: float | None = None,
        if_match: str | None = None,
        data_load_mode: bool | None = None,
    ) -> Any:
        return await self.request(
            "PATCH",
            self.url(entity, key=key),
            json_body=json,
            timeout=timeout,
            headers=self._write_headers(if_match=if_match, data_load_mode=data_load_mode),
        )

    async def put(
        self,
        entity: str,
        *,
        key: str | Mapping[str, str],
        json: Any,
        timeout: float | None = None,
        if_match: str | None = None,
        data_load_mode: bool | None = None,
    ) -> Any:
        return await self.request(
            "PUT",
            self.url(entity, key=key),
            json_body=json,
            timeout=timeout,
            headers=self._write_headers(if_match=if_match, data_load_mode=data_load_mode),
        )

    async def delete(
        self,
        entity: str,
        *,
        key: str | Mapping[str, str],
        timeout: float | None = None,
        if_match: str | None = None,
        data_load_mode: bool | None = None,
    ) -> Any:
        return await self.request(
            "DELETE",
            self.url(entity, key=key),
            timeout=timeout,
            headers=self._write_headers(if_match=if_match, data_load_mode=data_load_mode),
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
            if self.format == "atom":
                merged["Content-Type"] = _ATOM_CONTENT
                merged["DataServiceVersion"] = _ATOM_VERSION
                merged["MaxDataServiceVersion"] = _ATOM_VERSION
                kwargs["data"] = encode_entry(json_body).encode("utf-8")
            else:
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
            return self._decode_payload(text, response.headers.get("Content-Type", ""), response.status)

    def _decode_payload(self, text: str, content_type: str, status: int) -> Any:
        if self.format == "atom":
            return self._decode_atom(text, status)
        if self.format == "auto" and looks_like_xml_content_type(content_type):
            return self._decode_atom(text, status)
        try:
            return json.loads(text)
        except ValueError as exc:
            if self.format == "auto" and looks_like_atom(text):
                return self._decode_atom(text, status)
            raise ODataError(status, f"invalid JSON: {text[:200]}", body=text) from exc

    def _decode_atom(self, text: str, status: int) -> Any:
        try:
            return decode_atom(text)
        except (ElementTree.ParseError, ValueError) as exc:
            raise ODataError(status, f"invalid Atom: {text[:200]}", body=text) from exc

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
            try:
                self._apply_metadata(text)
            except ElementTree.ParseError:
                pass
            return text

    async def entity_sets(self, *, timeout: float | None = None) -> list[str]:
        await self._ensure_metadata(timeout=timeout)
        assert self._entity_set_names is not None
        return list(self._entity_set_names)

    async def has_entity_set(self, name: str, *, timeout: float | None = None) -> bool:
        await self._ensure_metadata(timeout=timeout)
        assert self._entity_set_names is not None
        return name in self._entity_set_names

    async def entity_type_for_set(self, name: str, *, timeout: float | None = None) -> EntityTypeInfo:
        await self._ensure_metadata(timeout=timeout)
        assert self._metadata_model is not None
        info = self._metadata_model.entity_type_for_set(name)
        if info is None:
            raise KeyError(name)
        return info

    def _write_headers(
        self,
        *,
        if_match: str | None = None,
        data_load_mode: bool | None = None,
    ) -> dict[str, str] | None:
        headers: dict[str, str] = {}
        if if_match is not None:
            headers["If-Match"] = if_match
        enabled = self.data_load_mode if data_load_mode is None else data_load_mode
        if enabled:
            headers[DATA_LOAD_MODE_HEADER] = "true"
        return headers or None

    def _apply_metadata(self, xml: str) -> None:
        self._metadata_model = parse_metadata(xml)
        self._entity_set_names = [info.name for info in self._metadata_model.entity_sets]

    async def _ensure_metadata(self, *, timeout: float | None = None) -> None:
        if self._metadata_model is not None:
            return
        await self.metadata(timeout=timeout)

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

"""Local stand-in for a published 1C infobase. Records what the client actually sent."""

from __future__ import annotations

import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer

from python_1c_odata import Infobase


class FakeOData:
    def __init__(self) -> None:
        self.requests: list[dict] = []
        self._next: tuple[int, object] = (200, {"value": []})
        self._queue: list[tuple[int, object]] = []
        self.base_url = ""

    def respond(self, status: int, payload: object) -> None:
        self._queue = []
        self._next = (status, payload)

    def respond_sequence(self, *responses: tuple[int, object]) -> None:
        self._queue = list(responses)
        if responses:
            self._next = responses[-1]

    async def handle(self, request: web.Request) -> web.StreamResponse:
        self.requests.append(
            {
                "method": request.method,
                "path": request.path,
                "query": request.query_string,
                "body": await request.read(),
                "authorization": request.headers.get("Authorization", ""),
                "content_type": request.headers.get("Content-Type", ""),
                "if_match": request.headers.get("If-Match", ""),
                "data_load_mode": request.headers.get("1C_OData-DataLoadMode", ""),
            }
        )
        if self._queue:
            status, payload = self._queue.pop(0)
            if not self._queue:
                self._next = (status, payload)
        else:
            status, payload = self._next
        if isinstance(payload, (bytes, str)):
            text = payload.decode() if isinstance(payload, bytes) else payload
            return web.Response(status=status, text=text, content_type="application/json")
        return web.json_response(payload, status=status)

    @property
    def last(self) -> dict:
        return self.requests[-1]


@pytest.fixture
async def fake_odata():
    fake = FakeOData()
    app = web.Application()
    app.router.add_route("*", "/{path:.*}", fake.handle)
    server = TestServer(app)
    await server.start_server()
    fake.base_url = str(server.make_url("/")).rstrip("/")
    yield fake
    await server.close()


@pytest.fixture
async def infobase(fake_odata):
    ib = Infobase(fake_odata.base_url, "ut", "user", "secret")
    async with ib:
        yield ib

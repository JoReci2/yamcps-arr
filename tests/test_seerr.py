"""Seerr contract tests using its documented API v1 wire shapes."""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx
from mcp import Client
from mcp.server import MCPServer
from pydantic import SecretStr
from support import create_service_server
from yamcps import ConnectorSecrets, SecretError
from yamcps.vault import Vault

from yamcps_arr.seerr import SeerrConnector
from yamcps_arr.seerr.client import SeerrClient, SeerrError, validate_url
from yamcps_arr.seerr.service import SeerrService

_KEY = "sentinel-seerr-key-93217"
_URL = "https://seerr.example.test/requests"
_VALUES = {"YAMCPS_ARR_SEERR_URL": _URL, "YAMCPS_ARR_SEERR_API_KEY": _KEY}
_RESOURCE = {"version": "1.0.0"}


class SeerrClientTests(unittest.IsolatedAsyncioTestCase):
    def client(self, handler):
        return SeerrClient(_URL, SecretStr(_KEY), transport=httpx.MockTransport(handler))

    async def test_header_prefix_timeout_and_no_credentials_in_url(self):
        requests = []

        def respond(request):
            requests.append(request)
            self.assertEqual(request.headers["X-Api-Key"], _KEY)
            self.assertEqual(str(request.url), _URL + "/api/v1/status")
            self.assertNotIn(_KEY, str(request.url))
            self.assertEqual(request.extensions["timeout"]["connect"], 5.0)
            self.assertEqual(request.extensions["timeout"]["read"], 15.0)
            return httpx.Response(200, json=_RESOURCE)

        self.assertEqual(await self.client(respond).object("status"), _RESOURCE)
        self.assertEqual(len(requests), 1)

    async def test_status_errors_do_not_echo_response_body_or_key(self):
        for status, message in [
            (400, "rejected"),
            (401, "authentication"),
            (403, "denied"),
            (404, "not found"),
            (409, "conflict"),
            (422, "rejected"),
            (429, "rate limit"),
            (503, "HTTP 503"),
        ]:
            with self.subTest(status=status):
                client = self.client(lambda request: httpx.Response(status, text=_KEY))
                with self.assertRaisesRegex(SeerrError, message) as error:
                    await client.object("system/status")
                self.assertNotIn(_KEY, str(error.exception))

    async def test_redirect_is_not_followed(self):
        seen = []

        def respond(request):
            seen.append(request)
            return httpx.Response(302, headers={"Location": "https://other.example.test/"})

        with self.assertRaisesRegex(SeerrError, "redirect"):
            await self.client(respond).object("system/status")
        self.assertEqual(len(seen), 1)

    async def test_timeouts_network_failures_and_invalid_json(self):
        for exception, expected in [
            (httpx.ReadTimeout, "timed out"),
            (httpx.ConnectError, "Cannot reach"),
        ]:

            def fail(request):
                raise exception(_KEY, request=request)

            with (
                self.subTest(exception=exception),
                self.assertRaisesRegex(SeerrError, expected) as error,
            ):
                await self.client(fail).object("system/status")
            self.assertNotIn(_KEY, str(error.exception))
        with self.assertRaisesRegex(SeerrError, "invalid JSON"):
            await self.client(lambda request: httpx.Response(200, text="<html>" + _KEY)).object(
                "system/status"
            )

    async def test_unexpected_shapes(self):
        for value, method in [([], "object"), ([1], "object")]:
            with self.subTest(value=value, method=method):
                client = self.client(lambda request: httpx.Response(200, json=value))
                with self.assertRaisesRegex(SeerrError, "unexpected"):
                    await getattr(client, method)("indexer")

    async def test_no_automatic_retry_on_timeout(self):
        seen = []

        def fail(request):
            seen.append(request)
            raise httpx.ReadTimeout("uncertain", request=request)

        with self.assertRaises(SeerrError):
            await self.client(fail).object("request", payload={"mediaType": "movie", "mediaId": 1})
        self.assertEqual(len(seen), 1)

    def test_url_and_key_validation(self):
        self.assertEqual(validate_url("http://localhost:5055/"), "http://localhost:5055")
        self.assertEqual(validate_url(_URL + "/"), _URL)
        for url in [
            "file:///tmp/seerr",
            "example.test",
            "https://user:pass@example.test",
            "https://example.test/?apiKey=secret",
            "https://example.test/#fragment",
            "https://example.test/api/v1/",
            "https://example.test/has space",
            "http://example.test:invalid",
            "https://example.test/\\wrong",
        ]:
            with self.subTest(url=url), self.assertRaises(SecretError):
                validate_url(url)
        for value in ["", "bad\r\nheader", "non ascii é"]:
            with self.subTest(value=value), self.assertRaises(SecretError):
                SeerrClient(_URL, SecretStr(value))


class SeerrWorkflowTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.requests = []
        self.user = {"id": 7, "email": "private@example.test", "plexToken": "unknown-token"}
        self.request = {
            "id": 12,
            "status": 1,
            "type": "tv",
            "is4k": False,
            "media": {"id": 8, "tmdbId": 99, "status": 2, "plexUrl": "private-url"},
            "requestedBy": self.user,
            "modifiedBy": self.user,
            "seasons": [{"id": 5, "seasonNumber": 1, "status": 1, "secret": "unknown-token"}],
            "rootFolder": "private-root",
        }
        self.media = {
            "id": 99,
            "mediaType": "tv",
            "name": "Example",
            "overview": _KEY,
            "mediaInfo": {"id": 8, "tmdbId": 99, "status": 2, "requests": [self.request]},
            "seasons": [{"id": 2, "seasonNumber": 1, "episodeCount": 10}],
        }
        self.client = SeerrClient(
            _URL, SecretStr(_KEY), transport=httpx.MockTransport(self.respond)
        )
        self.service = SeerrService(self.client, ConnectorSecrets("arr", _VALUES).redact)

    def respond(self, request):
        self.requests.append(request)
        route = request.url.path.removeprefix("/requests/api/v1/")
        if route == "status":
            data = {"version": "1.0.0", "apiKey": _KEY}
        elif route == "search":
            data = {
                "page": 2,
                "totalPages": 3,
                "totalResults": 41,
                "results": [self.media, {"id": 1, "mediaType": "person"}],
            }
        elif route in {"movie/99", "tv/99"}:
            data = self.media
        elif route == "request" and request.method == "GET":
            data = {
                "pageInfo": {"page": 2, "pages": 3, "results": 41, "pageSize": 20},
                "results": [self.request],
            }
        elif route in {"request", "request/12", "request/12/approve", "request/12/decline"}:
            data = self.request
        else:
            self.fail(f"Unexpected route: {route}")
        return httpx.Response(
            201 if request.method == "POST" and route == "request" else 200, json=data
        )

    def assert_safe(self, value):
        for secret in [
            _KEY,
            "unknown-token",
            "private@example.test",
            "private-root",
            "private-url",
        ]:
            self.assertNotIn(secret, repr(value))

    async def test_catalog_and_status_projection(self):
        self.assertEqual(await self.service.system_status(), {"version": "1.0.0"})
        self.assertEqual(self.requests[-1].url.params["checkUpdateAvailable"], "false")
        result = await self.service.search("Example", page=2)
        self.assertEqual(dict(self.requests[-1].url.params), {"query": "Example", "page": "2"})
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["overview"], "[REDACTED]")
        self.assert_safe(result)
        self.assert_safe(await self.service.get_movie(99))
        self.assert_safe(await self.service.get_tv(99))
        with self.assertRaises(SeerrError):
            await self.service.search("  ")

    async def test_request_filters_and_safe_nested_users(self):
        result = await self.service.list_requests(
            take=10, skip=20, status="pending", media_type="tv", requested_by=7
        )
        self.assertEqual(
            dict(self.requests[-1].url.params),
            {
                "take": "10",
                "skip": "20",
                "filter": "pending",
                "mediaType": "tv",
                "sort": "added",
                "sortDirection": "desc",
                "requestedBy": "7",
            },
        )
        self.assertEqual(result["results"][0]["requestedBy"], {"id": 7})
        self.assert_safe(result)
        self.assert_safe(await self.service.get_request(12))
        await self.service.list_requests()
        self.assertNotIn("requestedBy", self.requests[-1].url.params)

    async def test_create_payloads_and_explicit_seasons(self):
        for media_type, seasons, expected in [
            ("movie", None, {"mediaType": "movie", "mediaId": 99, "is4k": True}),
            ("tv", [0, 1, 1], {"mediaType": "tv", "mediaId": 99, "is4k": True, "seasons": [0, 1]}),
            ("tv", "all", {"mediaType": "tv", "mediaId": 99, "is4k": True, "seasons": "all"}),
        ]:
            self.assert_safe(await self.service.create_request(media_type, 99, seasons, is4k=True))
            self.assertEqual(self.requests[-1].method, "POST")
            self.assertEqual(json.loads(self.requests[-1].content), expected)
        count = len(self.requests)
        for media_type, seasons in [("tv", None), ("movie", [1])]:
            with self.assertRaises(SeerrError):
                await self.service.create_request(media_type, 99, seasons)
        self.assertEqual(len(self.requests), count)

    async def test_approval_and_decline_routes(self):
        for status in ["approve", "decline"]:
            self.assert_safe(await self.service.update_request_status(12, status))
            self.assertEqual(self.requests[-1].url.path, f"/requests/api/v1/request/12/{status}")
            self.assertEqual(self.requests[-1].method, "POST")

    async def test_unexpected_and_optional_nested_shapes(self):
        for value in [{}, {"results": None}, {"results": [1]}]:
            self.client._transport = httpx.MockTransport(
                lambda request: httpx.Response(200, json=value)
            )
            with self.assertRaises(SeerrError):
                await self.service.search("Example")
        for key in ["mediaInfo", "seasons"]:
            malformed = {**self.media, key: {"requests": [1]} if key == "mediaInfo" else [1]}
            with self.assertRaises(SeerrError):
                self.service._media(malformed)
        self.assertEqual(self.service._media({"title": {"token": "unknown-token"}}), {})
        self.assertEqual(
            self.service._request({"id": 12, "media": None, "modifiedBy": None}), {"id": 12}
        )
        self.assertEqual(self.service._media({"id": 99}), {"id": 99})

    async def test_mcp_schema_annotations_and_no_network_at_registration(self):
        with patch("yamcps_arr.seerr.SeerrClient", return_value=self.client):
            server = create_service_server(SeerrConnector, ["seerr"], secret_values=_VALUES)
        self.assertEqual(self.requests, [])
        async with Client(server) as client:
            tools = (await client.list_tools()).tools
            self.assertEqual(len(tools), 8)
            for tool in tools:
                mutation = tool.name in {
                    "arr_seerr_create_request",
                    "arr_seerr_update_request_status",
                }
                self.assertEqual(tool.annotations.read_only_hint, not mutation)
                self.assertEqual(tool.annotations.idempotent_hint, not mutation)
                self.assertNotIn("api_key", repr(tool.input_schema))
            resource = await client.read_resource("skill://arr-seerr-manage/SKILL.md")
            self.assertIn("arr_seerr_create_request", resource.contents[0].text)
            self.assertFalse(
                (await client.call_tool("arr_seerr_get_request", {"request_id": 12})).is_error
            )
            count = len(self.requests)
            for name, args in [
                ("get_request", {"request_id": 0}),
                ("search", {"query": "Example", "page": 0}),
                ("list_requests", {"take": 101}),
                ("list_requests", {"skip": -1}),
                ("list_requests", {"status": "invalid"}),
                ("create_request", {"media_type": "tv", "tmdb_id": 99, "seasons": []}),
                ("create_request", {"media_type": "tv", "tmdb_id": 99, "seasons": [-1]}),
                ("create_request", {"media_type": "tv", "tmdb_id": 99}),
                ("update_request_status", {"request_id": 12, "status": "delete"}),
            ]:
                with self.subTest(name=name, args=args):
                    self.assertTrue((await client.call_tool(f"arr_seerr_{name}", args)).is_error)
            self.assertEqual(len(self.requests), count)

    async def test_onboarding_and_headless_reuse(self):
        with tempfile.TemporaryDirectory() as directory:
            vault = Vault(Path(directory) / "vault", Path(directory) / "key")
            with (
                patch("yamcps_arr.seerr.SeerrClient", return_value=self.client),
                patch("sys.stdin.isatty", return_value=True),
                patch("yamcps.onboarding.getpass.getpass", side_effect=[_URL, _KEY]) as prompt,
                contextlib.redirect_stderr(io.StringIO()),
            ):
                create_service_server(SeerrConnector, ["seerr"], vault=vault, interactive=True)
            self.assertEqual(prompt.call_count, 2)
            self.assertEqual(self.requests, [])
            with patch("yamcps.onboarding.getpass.getpass") as prompt:
                create_service_server(SeerrConnector, ["seerr"], vault=vault)
            prompt.assert_not_called()

    def test_configuration_required(self):
        plugin = SeerrConnector()
        self.assertEqual(
            [spec.name for spec in plugin.required_secrets()], ["seerr-url", "seerr-api-key"]
        )
        with self.assertRaises(SecretError):
            plugin.register(MCPServer("test"))
        with self.assertRaises(SecretError):
            plugin.configure(ConnectorSecrets("arr", {}))


if __name__ == "__main__":
    unittest.main()

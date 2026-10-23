"""Integration checks for the unified installed ARR distribution."""

import asyncio
import os
import socket
import subprocess
import sys
import tempfile
import unittest
from importlib.metadata import entry_points
from pathlib import Path
from unittest.mock import patch

import httpx
from mcp import Client, StdioServerParameters
from yamcps import ConnectorSecrets, SecretError
from yamcps.server import create_server
from yamcps.vault import Vault

from yamcps_arr import ArrConnector
from yamcps_arr.prowlarr.client import ProwlarrClient
from yamcps_arr.radarr.client import RadarrClient
from yamcps_arr.sonarr.client import SonarrClient

_VALUES = {
    f"YAMCPS_ARR_{service.upper()}_{field}": value
    for service in ("sonarr", "radarr", "prowlarr")
    for field, value in (
        ("URL", f"http://{service}.example.test"),
        ("API_KEY", f"test-{service}-token"),
    )
}


class ArrTests(unittest.IsolatedAsyncioTestCase):
    def test_entry_point_and_required_fields(self):
        entries = [
            entry for entry in entry_points(group="yamcps.connectors") if entry.name == "arr"
        ]
        self.assertEqual(len(entries), 1)
        self.assertIsInstance(entries[0].load()(), ArrConnector)
        plugin = ArrConnector()
        self.assertEqual(
            {spec.name for spec in plugin.required_secrets()},
            {
                f"{service}-{field}"
                for service in ("sonarr", "radarr", "prowlarr")
                for field in ("url", "api-key")
            },
        )
        for key in _VALUES:
            with self.subTest(key=key), self.assertRaises(SecretError):
                plugin.configure(
                    ConnectorSecrets("arr", {k: v for k, v in _VALUES.items() if k != key})
                )
        with self.assertRaises(ValueError):
            create_server(["arr", "arr"], secret_values=_VALUES)

    async def exercise(self, target):
        async with Client(target) as client:
            tools = (await client.list_tools()).tools
            self.assertEqual(len(tools), 34)
            self.assertEqual(len({tool.name for tool in tools}), 34)
            self.assertTrue(all(tool.name.startswith("arr_") for tool in tools))
            for skill in ("arr-sonarr-manage", "arr-radarr-manage", "arr-prowlarr-search"):
                result = await client.read_resource(f"skill://{skill}/SKILL.md")
                self.assertIn(f"name: {skill}", result.contents[0].text)
            self.assertTrue(
                (await client.call_tool("arr_sonarr_get_series", {"series_id": 0})).is_error
            )

    async def test_memory_and_shared_secret_redaction(self):
        def respond(request):
            return httpx.Response(200, json={"version": _VALUES["YAMCPS_ARR_RADARR_API_KEY"]})

        transport = httpx.MockTransport(respond)
        with (
            patch(
                "yamcps_arr.sonarr.SonarrClient",
                side_effect=lambda url, key: SonarrClient(url, key, transport=transport),
            ),
            patch(
                "yamcps_arr.radarr.RadarrClient",
                side_effect=lambda url, key: RadarrClient(url, key, transport=transport),
            ),
            patch(
                "yamcps_arr.prowlarr.ProwlarrClient",
                side_effect=lambda url, key: ProwlarrClient(url, key, transport=transport),
            ),
        ):
            server = create_server(["arr"], secret_values=_VALUES)
        await self.exercise(server)
        async with Client(server) as client:
            for service in ("sonarr", "radarr", "prowlarr"):
                result = await client.call_tool(f"arr_{service}_system_status", {})
                self.assertFalse(result.is_error)
                self.assertNotIn("test-radarr-token", repr(result))
                self.assertIn("[REDACTED]", repr(result))

    def server_args(self, directory):
        vault = Vault(Path(directory) / "vault", Path(directory) / "key")
        vault.initialize()
        vault.update(_VALUES)
        return [
            "-m",
            "yamcps",
            "serve",
            "--connector",
            "arr",
            "--vault",
            str(vault.path),
            "--key-file",
            str(vault.key_file),
            "--config-file",
            str(Path(directory) / "config.json"),
        ]

    async def test_stdio(self):
        with tempfile.TemporaryDirectory() as directory:
            await self.exercise(
                StdioServerParameters(
                    command=sys.executable,
                    args=self.server_args(directory),
                    env={**os.environ, **_VALUES},
                )
            )

    async def test_http_loopback(self):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        with tempfile.TemporaryDirectory() as directory:
            with subprocess.Popen(
                [
                    sys.executable,
                    *self.server_args(directory),
                    "--transport",
                    "http",
                    "--port",
                    str(port),
                ],
                env={**os.environ, **_VALUES},
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            ) as process:
                try:
                    async with httpx.AsyncClient(trust_env=False) as probe:
                        for _ in range(100):
                            if process.poll() is not None:
                                self.fail("HTTP server exited during startup")
                            try:
                                await probe.get(f"http://127.0.0.1:{port}/mcp")
                                break
                            except httpx.ConnectError:
                                await asyncio.sleep(0.1)
                        else:
                            self.fail("HTTP server did not start")
                    await self.exercise(f"http://127.0.0.1:{port}/mcp")
                finally:
                    process.terminate()
                    process.wait(timeout=10)


if __name__ == "__main__":
    unittest.main()

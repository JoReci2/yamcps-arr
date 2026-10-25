"""Integration checks for the unified installed ARR distribution."""

import asyncio
import contextlib
import io
import os
import socket
import subprocess
import sys
import tempfile
import unittest
from importlib.metadata import entry_points
from itertools import combinations
from pathlib import Path
from unittest.mock import patch

import httpx
from mcp import Client, StdioServerParameters
from mcp.server import MCPServer
from yamcps import ConfigError, ConnectorConfigs, ConnectorSecrets, SecretError
from yamcps.configs import ConfigStore
from yamcps.server import create_server
from yamcps.vault import Vault

from yamcps_arr import ArrConnector
from yamcps_arr.prowlarr.client import ProwlarrClient
from yamcps_arr.radarr.client import RadarrClient
from yamcps_arr.seerr.client import SeerrClient
from yamcps_arr.sonarr.client import SonarrClient

_VALUES = {
    f"YAMCPS_ARR_{service.upper()}_{field}": value
    for service in ("sonarr", "radarr", "prowlarr", "seerr")
    for field, value in (
        ("URL", f"http://{service}.example.test"),
        ("API_KEY", f"test-{service}-token"),
    )
}

_CONFIG = {
    f"YAMCPS_ARR_ENABLED_{name.upper()}": "true"
    for name in ("sonarr", "radarr", "prowlarr", "seerr")
}


class ArrTests(unittest.IsolatedAsyncioTestCase):
    async def test_all_fifteen_service_combinations(self):
        counts = {"sonarr": 13, "radarr": 11, "prowlarr": 10, "seerr": 8}
        skills = {
            "sonarr": "arr-sonarr-manage",
            "radarr": "arr-radarr-manage",
            "prowlarr": "arr-prowlarr-search",
            "seerr": "arr-seerr-manage",
        }
        for size in range(1, 5):
            for selected in combinations(counts, size):
                with self.subTest(selected=selected):
                    configs = {
                        f"YAMCPS_ARR_ENABLED_{name.upper()}": " TrUe "
                        for name in reversed(selected)
                    }
                    values = {
                        key: value
                        for key, value in _VALUES.items()
                        if any(key.startswith(f"YAMCPS_ARR_{name.upper()}_") for name in selected)
                    }
                    plugin = ArrConnector()
                    self.assertEqual(
                        [
                            spec.name
                            for spec in plugin.required_secrets_for_configs(
                                ConnectorConfigs("arr", configs)
                            )
                        ],
                        [f"{name}-{field}" for name in selected for field in ("url", "api-key")],
                    )
                    with patch("httpx.AsyncClient.request", side_effect=AssertionError("network")):
                        server = create_server(["arr"], config_values=configs, secret_values=values)
                    async with Client(server) as client:
                        tools = (await client.list_tools()).tools
                        resources = (await client.list_resources()).resources
                        self.assertEqual(
                            {str(resource.uri) for resource in resources},
                            {f"skill://{skills[name]}/SKILL.md" for name in selected},
                        )
                        self.assertEqual(len(tools), sum(counts[name] for name in selected))
                        self.assertEqual({tool.name.split("_")[1] for tool in tools}, set(selected))
                        for name in selected:
                            resource = await client.read_resource(
                                f"skill://{skills[name]}/SKILL.md"
                            )
                            self.assertIn(f"name: {skills[name]}", resource.contents[0].text)
                    plugin.configure(ConnectorSecrets("arr", values))
                    plugin.configure_configs(ConnectorConfigs("arr", configs))
                    self.assertEqual(
                        [root.name for root in plugin.skill_roots()],
                        [skills[name] for name in selected],
                    )

    def test_selection_validation_and_unconfigured_lifecycle(self):
        plugin = ArrConnector()
        self.assertTrue(all(spec.default == "false" for spec in plugin.required_configs()))
        for value in [
            "",
            " ",
            "sonarr,",
            ",sonarr",
            "sonarr,,seerr",
            "unknown",
            "1",
            "yes",
            "sonarr,SONARR",
            "all",
            "none",
        ]:
            with self.subTest(value=value), self.assertRaises(ConfigError):
                plugin.required_secrets_for_configs(
                    ConnectorConfigs("arr", {"YAMCPS_ARR_ENABLED_SONARR": value})
                )
        with self.assertRaises(ValueError):
            create_server(["arr"], secret_values=_VALUES, config_values={})
        with self.assertRaises(ConfigError):
            plugin.required_secrets_for_configs(
                ConnectorConfigs("arr", {key: " FaLsE " for key in _CONFIG})
            )
        with self.assertRaises(ConfigError):
            plugin.register(MCPServer("test"))
        with self.assertRaises(SecretError):
            plugin.configure_configs(ConnectorConfigs("arr", _CONFIG))
        self.assertEqual(list(plugin.skill_roots()), [])

    async def test_disabled_credentials_ignored_but_still_redacted(self):
        values = {**_VALUES, "YAMCPS_ARR_RADARR_URL": "invalid URL"}
        transport = httpx.MockTransport(
            lambda request: httpx.Response(
                200, json={"version": _VALUES["YAMCPS_ARR_RADARR_API_KEY"]}
            )
        )
        with (
            patch(
                "yamcps_arr.sonarr.SonarrClient",
                side_effect=lambda url, key: SonarrClient(url, key, transport=transport),
            ),
            patch("yamcps_arr.radarr.RadarrClient", side_effect=AssertionError("disabled")),
        ):
            server = create_server(
                ["arr"],
                secret_values=values,
                config_values={"YAMCPS_ARR_ENABLED_SONARR": " true "},
            )
        async with Client(server) as client:
            result = await client.call_tool("arr_sonarr_system_status", {})
            self.assertFalse(result.is_error)
            self.assertNotIn(_VALUES["YAMCPS_ARR_RADARR_API_KEY"], repr(result))
            self.assertIn("[REDACTED]", repr(result))

    def test_vault_prompts_only_active_secrets_and_reuses_on_reactivation(self):
        with tempfile.TemporaryDirectory() as directory:
            vault = Vault(Path(directory) / "vault", Path(directory) / "key")
            configs = {"YAMCPS_ARR_ENABLED_SONARR": "true"}
            values = [_VALUES["YAMCPS_ARR_SONARR_URL"], _VALUES["YAMCPS_ARR_SONARR_API_KEY"]]
            with (
                patch("sys.stdin.isatty", return_value=True),
                patch("yamcps.onboarding.getpass.getpass", side_effect=values) as prompt,
                contextlib.redirect_stderr(io.StringIO()),
            ):
                create_server(["arr"], config_values=configs, vault=vault, interactive=True)
            self.assertEqual(prompt.call_count, 2)
            self.assertEqual(
                set(vault.values()), {"YAMCPS_ARR_SONARR_URL", "YAMCPS_ARR_SONARR_API_KEY"}
            )
            vault.update(_VALUES)
            before = vault.values()
            with patch("yamcps.onboarding.getpass.getpass") as prompt:
                create_server(["arr"], config_values=configs, vault=vault)
                create_server(["arr"], config_values=_CONFIG, vault=vault)
            prompt.assert_not_called()
            self.assertEqual(vault.values(), before)

    def test_invalid_selection_never_prompts_for_secrets(self):
        with tempfile.TemporaryDirectory() as directory:
            vault = Vault(Path(directory) / "vault", Path(directory) / "key")
            with patch("yamcps.onboarding.getpass.getpass") as prompt:
                for config in [{}, {"YAMCPS_ARR_ENABLED_SONARR": "unknown"}]:
                    with self.assertRaises(ValueError):
                        create_server(["arr"], config_values=config, vault=vault)
            prompt.assert_not_called()
            self.assertFalse(vault.path.exists())

    def test_cli_secrets_follow_config_file_and_reject_inactive_names(self):
        from yamcps.cli import main

        with tempfile.TemporaryDirectory() as directory:
            store = ConfigStore(Path(directory) / "config.json")
            store.set("arr", "enabled-seerr", "true")
            vault = Vault(Path(directory) / "vault", Path(directory) / "key")
            args = [
                "yamcps",
                "secrets",
                "set",
                "--connector",
                "arr",
                "--config-file",
                str(store.path),
                "--vault",
                str(vault.path),
                "--key-file",
                str(vault.key_file),
            ]
            with (
                patch("sys.argv", args),
                patch("sys.stdin.isatty", return_value=True),
                patch(
                    "yamcps.onboarding.getpass.getpass",
                    side_effect=[
                        _VALUES["YAMCPS_ARR_SEERR_URL"],
                        _VALUES["YAMCPS_ARR_SEERR_API_KEY"],
                    ],
                ) as prompt,
                contextlib.redirect_stderr(io.StringIO()),
            ):
                main()
            self.assertEqual(prompt.call_count, 2)
            self.assertEqual(
                set(vault.values()), {"YAMCPS_ARR_SEERR_URL", "YAMCPS_ARR_SEERR_API_KEY"}
            )
            with (
                patch("sys.argv", args + ["--name", "sonarr-api-key"]),
                patch("yamcps.onboarding.getpass.getpass") as prompt,
                contextlib.redirect_stderr(io.StringIO()),
            ):
                with self.assertRaises(SystemExit) as error:
                    main()
            self.assertEqual(error.exception.code, 2)
            prompt.assert_not_called()

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
                for service in ("sonarr", "radarr", "prowlarr", "seerr")
                for field in ("url", "api-key")
            },
        )
        for key in _VALUES:
            with self.subTest(key=key), self.assertRaises(SecretError):
                plugin.configure(
                    ConnectorSecrets("arr", {k: v for k, v in _VALUES.items() if k != key})
                )
                plugin.configure_configs(ConnectorConfigs("arr", _CONFIG))
        with self.assertRaises(ValueError):
            create_server(["arr", "arr"], secret_values=_VALUES)

    async def exercise(self, target, selected=("sonarr", "radarr", "prowlarr", "seerr")):
        async with Client(target) as client:
            tools = (await client.list_tools()).tools
            counts = {"sonarr": 13, "radarr": 11, "prowlarr": 10, "seerr": 8}
            expected = sum(counts[name] for name in selected)
            self.assertEqual(len(tools), expected)
            self.assertEqual(len({tool.name for tool in tools}), expected)
            self.assertEqual({tool.name.split("_")[1] for tool in tools}, set(selected))
            self.assertTrue(all(tool.name.startswith("arr_") for tool in tools))
            for skill in (
                "arr-sonarr-manage",
                "arr-radarr-manage",
                "arr-prowlarr-search",
                "arr-seerr-manage",
            ):
                if skill.split("-")[1] not in selected:
                    continue
                result = await client.read_resource(f"skill://{skill}/SKILL.md")
                self.assertIn(f"name: {skill}", result.contents[0].text)
            if "sonarr" in selected:
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
            patch(
                "yamcps_arr.seerr.SeerrClient",
                side_effect=lambda url, key: SeerrClient(url, key, transport=transport),
            ),
        ):
            server = create_server(["arr"], secret_values=_VALUES, config_values=_CONFIG)
        await self.exercise(server)
        async with Client(server) as client:
            for service in ("sonarr", "radarr", "prowlarr", "seerr"):
                result = await client.call_tool(f"arr_{service}_system_status", {})
                self.assertFalse(result.is_error)
                self.assertNotIn("test-radarr-token", repr(result))
                self.assertIn("[REDACTED]", repr(result))

    def server_args(self, directory, selected=("sonarr", "radarr", "prowlarr", "seerr")):
        vault = Vault(Path(directory) / "vault", Path(directory) / "key")
        vault.initialize()
        vault.update(_VALUES)
        store = ConfigStore(Path(directory) / "config.json")
        for name in selected:
            store.set("arr", f"enabled-{name}", "true")
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
        for selected in [("sonarr", "radarr", "prowlarr", "seerr"), ("seerr",)]:
            with tempfile.TemporaryDirectory() as directory:
                await self.exercise(
                    StdioServerParameters(
                        command=sys.executable,
                        args=self.server_args(directory, selected),
                        env={**os.environ, **_VALUES},
                    ),
                    selected,
                )

    async def test_http_loopback(self):
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        with tempfile.TemporaryDirectory() as directory:
            with subprocess.Popen(
                [
                    sys.executable,
                    *self.server_args(directory, ("sonarr", "seerr")),
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
                    await self.exercise(f"http://127.0.0.1:{port}/mcp", ("sonarr", "seerr"))
                finally:
                    process.terminate()
                    process.wait(timeout=10)


if __name__ == "__main__":
    unittest.main()

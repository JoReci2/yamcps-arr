"""Unified ARR connector with packaged services and vault-backed credentials."""

from collections.abc import Iterable
from pathlib import Path

from mcp.server import MCPServer
from yamcps import ConnectorSecrets, SecretSpec

from yamcps_arr.prowlarr import ProwlarrConnector
from yamcps_arr.radarr import RadarrConnector
from yamcps_arr.sonarr import SonarrConnector


class ArrConnector:
    """Expose Sonarr, Radarr and Prowlarr through one connector."""

    id = "arr"

    def __init__(self) -> None:
        """Create service adapters without network access."""
        self._adapters = (SonarrConnector(), RadarrConnector(), ProwlarrConnector())

    def required_secrets(self) -> list[SecretSpec]:
        """Return the six service settings required in the ARR vault scope."""
        return [spec for adapter in self._adapters for spec in adapter.required_secrets()]

    def configure(self, secrets: ConnectorSecrets) -> None:
        """Configure all services without contacting their instances.

        Args:
            secrets: ARR-scoped credentials shared for complete output redaction.
        """
        for adapter in self._adapters:
            adapter.configure(secrets)

    def register(self, server: MCPServer) -> None:
        """Register all service tools with their operation annotations.

        Args:
            server: MCP server receiving the ARR tools.
        """
        for adapter in self._adapters:
            adapter.register(server)

    def skill_roots(self) -> Iterable[Path]:
        """Return all bundled ARR workflow skill roots."""
        return [root for adapter in self._adapters for root in adapter.skill_roots()]

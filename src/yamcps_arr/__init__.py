"""Unified ARR connector with packaged services and vault-backed credentials."""

from collections.abc import Iterable
from pathlib import Path

from mcp.server import MCPServer
from yamcps import (
    ConfigError,
    ConfigSpec,
    ConnectorConfigs,
    ConnectorSecrets,
    SecretError,
    SecretSpec,
)

from yamcps_arr.prowlarr import ProwlarrConnector
from yamcps_arr.radarr import RadarrConnector
from yamcps_arr.seerr import SeerrConnector
from yamcps_arr.sonarr import SonarrConnector


class ArrConnector:
    """Expose Sonarr, Radarr, Prowlarr and Seerr through one connector."""

    id = "arr"

    def __init__(self) -> None:
        """Create service adapters without network access."""
        self._adapters: dict[
            str, SonarrConnector | RadarrConnector | ProwlarrConnector | SeerrConnector
        ] = {
            "sonarr": SonarrConnector(),
            "radarr": RadarrConnector(),
            "prowlarr": ProwlarrConnector(),
            "seerr": SeerrConnector(),
        }
        self._enabled: tuple[str, ...] = ()
        self._secrets: ConnectorSecrets | None = None

    def required_configs(self) -> list[ConfigSpec]:
        """Declare one opt-in boolean setting per service."""
        return [
            ConfigSpec(f"enabled-{name}", f"Enable {name}: true or false", default="false")
            for name in self._adapters
        ]

    def _selection(self, configs: ConnectorConfigs) -> tuple[str, ...]:
        selected = []
        for name in self._adapters:
            value = configs.get(f"enabled-{name}")
            normalized = "false" if value is None else value.strip().lower()
            if normalized not in {"true", "false"}:
                raise ConfigError(f"enabled-{name} must be true or false")
            if normalized == "true":
                selected.append(name)
        if not selected:
            raise ConfigError("Enable at least one ARR service with enabled-<service>=true")
        return tuple(selected)

    def required_secrets(self) -> list[SecretSpec]:
        """Return the complete eight-secret catalogue, including disabled services."""
        return [spec for adapter in self._adapters.values() for spec in adapter.required_secrets()]

    def required_secrets_for_configs(self, configs: ConnectorConfigs) -> list[SecretSpec]:
        """Select secrets without depending on configuration injection.

        Args:
            configs: Resolved ARR settings supplied before secret collection.

        Returns:
            Only the selected services' secret declarations, in canonical order.
        """
        return [
            spec
            for name in self._selection(configs)
            for spec in self._adapters[name].required_secrets()
        ]

    def configure(self, secrets: ConnectorSecrets) -> None:
        """Retain shared credentials until service selection is injected.

        Args:
            secrets: ARR-scoped credentials shared for complete output redaction.
        """
        self._secrets = secrets
        self._enabled = ()

    def configure_configs(self, configs: ConnectorConfigs) -> None:
        """Configure selected adapters without validating disabled credentials.

        Args:
            configs: Explicit service selection resolved by yamcps.

        Raises:
            SecretError: Credentials were not injected or an active secret is missing.
        """
        self._enabled = ()
        selected = self._selection(configs)
        if self._secrets is None:
            raise SecretError("Configure ARR credentials before selecting services")
        for name in selected:
            self._adapters[name].configure(self._secrets)
        self._enabled = selected

    def register(self, server: MCPServer) -> None:
        """Register all service tools with their operation annotations.

        Args:
            server: MCP server receiving the ARR tools.
        """
        if not self._enabled:
            raise ConfigError(
                "Enable and configure at least one service before registering ARR tools"
            )
        for name in self._enabled:
            self._adapters[name].register(server)

    def skill_roots(self) -> Iterable[Path]:
        """Return only enabled services' bundled workflow skill roots."""
        return [root for name in self._enabled for root in self._adapters[name].skill_roots()]

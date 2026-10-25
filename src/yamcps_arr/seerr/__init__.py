"""Seerr connector with vault-backed credentials and an embedded skill."""

from collections.abc import Iterable
from pathlib import Path

from mcp.server import MCPServer
from mcp.types import ToolAnnotations
from yamcps import ConnectorSecrets, SecretError, SecretSpec

from yamcps_arr.seerr.client import SeerrClient
from yamcps_arr.seerr.service import SeerrService


class SeerrConnector:
    """Expose media discovery and request management through Seerr API v1."""

    id = "arr"

    def __init__(self) -> None:
        """Create an unconfigured instance without network access."""
        self._service: SeerrService | None = None

    def required_secrets(self) -> list[SecretSpec]:
        """Describe instance settings collected by yamcps's terminal wizard.

        Returns:
            Instance URL and API key stored together in the encrypted vault.
        """
        return [
            SecretSpec(
                "seerr-url", "Seerr instance URL, e.g. http://localhost:5055 (without /api/v1)"
            ),
            SecretSpec("seerr-api-key", "Seerr API key (Settings > General)"),
        ]

    def configure(self, secrets: ConnectorSecrets) -> None:
        """Validate settings and create the API service without making a request.

        Args:
            secrets: Values scoped to this Seerr connector.
        """
        self._service = SeerrService(
            SeerrClient(
                secrets.require("seerr-url").get_secret_value(), secrets.require("seerr-api-key")
            ),
            secrets.redact,
        )

    def register(self, server: MCPServer) -> None:
        """Register fixed Seerr operations with read/write annotations.

        Args:
            server: MCP server receiving the tools.

        Raises:
            SecretError: The connector has not been configured.
        """
        if self._service is None:
            raise SecretError("Configure Seerr before registering its tools")
        read_only = [
            "system_status",
            "search",
            "get_movie",
            "get_tv",
            "list_requests",
            "get_request",
        ]
        mutations = ["create_request", "update_request_status"]
        for name in read_only + mutations:
            is_read = name in read_only
            server.add_tool(
                getattr(self._service, name),
                name=f"arr_seerr_{name}",
                annotations=ToolAnnotations(
                    read_only_hint=is_read,
                    destructive_hint=name == "update_request_status",
                    idempotent_hint=is_read,
                    open_world_hint=True,
                ),
            )

    def skill_roots(self) -> Iterable[Path]:
        """Locate the packaged Seerr workflow instructions.

        Returns:
            The seerr-manage skill directory.
        """
        return [Path(__file__).parent / "skills" / "arr-seerr-manage"]

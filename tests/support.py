"""Compose individual internal adapters for focused service regression tests."""

from unittest.mock import patch

from yamcps.server import create_server


def create_service_server(adapter, names, **kwargs):
    """Exercise the engine lifecycle with one internal service adapter."""
    with patch("yamcps.server.load", return_value=[adapter()]):
        return create_server(["arr"], **kwargs)

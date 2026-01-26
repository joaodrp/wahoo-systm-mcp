"""Tests for CLI entry points."""

from __future__ import annotations

import importlib
from unittest.mock import patch

import pytest

import wahoo_systm_mcp.__main__ as stdio_main
import wahoo_systm_mcp.main as http_main


class TestStdioEntrypoint:
    """Tests for __main__.py entry point (stdio transport)."""

    def test_missing_username_exits_with_error(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Exit with error when WAHOO_USERNAME is missing."""
        monkeypatch.delenv("WAHOO_USERNAME", raising=False)
        monkeypatch.setenv("WAHOO_PASSWORD", "test-password")

        # Reload to pick up env changes
        importlib.reload(stdio_main)

        with pytest.raises(SystemExit) as exc_info:
            stdio_main.main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Missing Wahoo SYSTM credentials" in captured.err
        assert "WAHOO_USERNAME" in captured.err

    def test_missing_password_exits_with_error(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Exit with error when WAHOO_PASSWORD is missing."""
        monkeypatch.setenv("WAHOO_USERNAME", "test-user")
        monkeypatch.delenv("WAHOO_PASSWORD", raising=False)

        importlib.reload(stdio_main)

        with pytest.raises(SystemExit) as exc_info:
            stdio_main.main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Missing Wahoo SYSTM credentials" in captured.err
        assert "WAHOO_PASSWORD" in captured.err

    def test_missing_both_credentials_exits_with_error(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Exit with error when both credentials are missing."""
        monkeypatch.delenv("WAHOO_USERNAME", raising=False)
        monkeypatch.delenv("WAHOO_PASSWORD", raising=False)

        importlib.reload(stdio_main)

        with pytest.raises(SystemExit) as exc_info:
            stdio_main.main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Missing Wahoo SYSTM credentials" in captured.err

    def test_valid_credentials_calls_mcp_run(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Call mcp.run() when credentials are present."""
        monkeypatch.setenv("WAHOO_USERNAME", "test-user")
        monkeypatch.setenv("WAHOO_PASSWORD", "test-password")

        importlib.reload(stdio_main)

        with patch.object(stdio_main, "mcp") as mock_mcp:
            stdio_main.main()
            mock_mcp.run.assert_called_once()


class TestHttpEntrypoint:
    """Tests for main.py entry point (HTTP transport)."""

    def test_missing_username_exits_with_error(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Exit with error when WAHOO_USERNAME is missing."""
        monkeypatch.delenv("WAHOO_USERNAME", raising=False)
        monkeypatch.setenv("WAHOO_PASSWORD", "test-password")

        importlib.reload(http_main)

        with pytest.raises(SystemExit) as exc_info:
            http_main.main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Missing Wahoo SYSTM credentials" in captured.err
        assert "WAHOO_USERNAME" in captured.err

    def test_missing_password_exits_with_error(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Exit with error when WAHOO_PASSWORD is missing."""
        monkeypatch.setenv("WAHOO_USERNAME", "test-user")
        monkeypatch.delenv("WAHOO_PASSWORD", raising=False)

        importlib.reload(http_main)

        with pytest.raises(SystemExit) as exc_info:
            http_main.main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Missing Wahoo SYSTM credentials" in captured.err
        assert "WAHOO_PASSWORD" in captured.err

    def test_valid_credentials_calls_mcp_run(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Call mcp.run() with HTTP transport when credentials are present."""
        monkeypatch.setenv("WAHOO_USERNAME", "test-user")
        monkeypatch.setenv("WAHOO_PASSWORD", "test-password")

        importlib.reload(http_main)

        with patch.object(http_main, "mcp") as mock_mcp:
            http_main.main()
            mock_mcp.run.assert_called_once()
            # Verify HTTP transport args
            call_kwargs = mock_mcp.run.call_args.kwargs
            assert "transport" in call_kwargs
            assert "host" in call_kwargs
            assert "port" in call_kwargs

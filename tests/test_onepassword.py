"""Tests for 1Password integration module."""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from wahoo_systm_mcp.onepassword import (
    CredentialsError,
    get_credentials,
    get_credentials_from_1password,
)


class TestGetCredentialsFrom1Password:
    """Tests for get_credentials_from_1password function."""

    def test_success(self) -> None:
        """Test successful credential retrieval from 1Password."""
        mock_username_result = MagicMock()
        mock_username_result.stdout = "test@example.com\n"

        mock_password_result = MagicMock()
        mock_password_result.stdout = "supersecret\n"

        with patch("wahoo_systm_mcp.onepassword.subprocess.run") as mock_run:
            mock_run.side_effect = [mock_username_result, mock_password_result]

            username, password = get_credentials_from_1password(
                "op://vault/item/username", "op://vault/item/password"
            )

            assert username == "test@example.com"
            assert password == "supersecret"
            assert mock_run.call_count == 2
            mock_run.assert_any_call(
                ["op", "read", "op://vault/item/username"],
                capture_output=True,
                text=True,
                check=True,
            )
            mock_run.assert_any_call(
                ["op", "read", "op://vault/item/password"],
                capture_output=True,
                text=True,
                check=True,
            )

    def test_subprocess_failure(self) -> None:
        """Test that subprocess failure raises CredentialsError."""
        error = subprocess.CalledProcessError(1, "op")
        error.stderr = "item not found"

        with patch("wahoo_systm_mcp.onepassword.subprocess.run") as mock_run:
            mock_run.side_effect = error

            with pytest.raises(CredentialsError) as exc_info:
                get_credentials_from_1password(
                    "op://vault/item/username", "op://vault/item/password"
                )

            assert "Failed to retrieve credentials from 1Password" in str(exc_info.value)
            assert "item not found" in str(exc_info.value)
            assert "Make sure you're signed in to 1Password" in str(exc_info.value)

    def test_subprocess_failure_without_stderr(self) -> None:
        """Test subprocess failure when stderr is empty."""
        error = subprocess.CalledProcessError(1, "op")
        error.stderr = ""

        with patch("wahoo_systm_mcp.onepassword.subprocess.run") as mock_run:
            mock_run.side_effect = error

            with pytest.raises(CredentialsError) as exc_info:
                get_credentials_from_1password(
                    "op://vault/item/username", "op://vault/item/password"
                )

            assert "Failed to retrieve credentials from 1Password" in str(exc_info.value)

    def test_cli_not_found(self) -> None:
        """Test missing 1Password CLI."""
        with patch("wahoo_systm_mcp.onepassword.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()

            with pytest.raises(CredentialsError) as exc_info:
                get_credentials_from_1password(
                    "op://vault/item/username", "op://vault/item/password"
                )

            assert "1Password CLI not found" in str(exc_info.value)


class TestGetCredentials:
    """Tests for get_credentials function."""

    def test_with_1password_refs(self) -> None:
        """Test credential retrieval using 1Password references."""
        mock_username_result = MagicMock()
        mock_username_result.stdout = "user@wahoo.com\n"

        mock_password_result = MagicMock()
        mock_password_result.stdout = "wahoopass\n"

        env_vars = {
            "WAHOO_USERNAME_1P_REF": "op://vault/wahoo/username",
            "WAHOO_PASSWORD_1P_REF": "op://vault/wahoo/password",
        }

        with (
            patch.dict("os.environ", env_vars, clear=True),
            patch("wahoo_systm_mcp.onepassword.subprocess.run") as mock_run,
        ):
            mock_run.side_effect = [mock_username_result, mock_password_result]

            username, password = get_credentials()

            assert username == "user@wahoo.com"
            assert password == "wahoopass"

    def test_fallback_to_plain_env_vars(self) -> None:
        """Test fallback to plain environment variables when 1Password refs missing."""
        env_vars = {
            "WAHOO_USERNAME": "plain_user@example.com",
            "WAHOO_PASSWORD": "plain_password",
        }

        with patch.dict("os.environ", env_vars, clear=True):
            username, password = get_credentials()

            assert username == "plain_user@example.com"
            assert password == "plain_password"

    def test_1password_takes_precedence(self) -> None:
        """Test that 1Password refs take precedence over plain env vars."""
        mock_username_result = MagicMock()
        mock_username_result.stdout = "1p_user@example.com\n"

        mock_password_result = MagicMock()
        mock_password_result.stdout = "1p_password\n"

        env_vars = {
            "WAHOO_USERNAME_1P_REF": "op://vault/wahoo/username",
            "WAHOO_PASSWORD_1P_REF": "op://vault/wahoo/password",
            "WAHOO_USERNAME": "plain_user@example.com",
            "WAHOO_PASSWORD": "plain_password",
        }

        with (
            patch.dict("os.environ", env_vars, clear=True),
            patch("wahoo_systm_mcp.onepassword.subprocess.run") as mock_run,
        ):
            mock_run.side_effect = [mock_username_result, mock_password_result]

            username, password = get_credentials()

            assert username == "1p_user@example.com"
            assert password == "1p_password"

    def test_raises_value_error_when_no_credentials(self) -> None:
        """Test that ValueError is raised when no credentials are found."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                get_credentials()

            error_msg = str(exc_info.value)
            assert "No credentials found" in error_msg
            assert "WAHOO_USERNAME_1P_REF" in error_msg
            assert "WAHOO_PASSWORD_1P_REF" in error_msg
            assert "WAHOO_USERNAME" in error_msg
            assert "WAHOO_PASSWORD" in error_msg

    def test_raises_value_error_with_partial_plain_credentials(self) -> None:
        """Test that ValueError is raised when only partial plain credentials exist."""
        env_vars = {"WAHOO_USERNAME": "user@example.com"}

        with patch.dict("os.environ", env_vars, clear=True):
            with pytest.raises(ValueError) as exc_info:
                get_credentials()

            assert "No credentials found" in str(exc_info.value)

    def test_raises_value_error_with_partial_1password_refs(self) -> None:
        """Test that partial 1Password refs fall through to plain env check."""
        env_vars = {
            "WAHOO_USERNAME_1P_REF": "op://vault/wahoo/username",
            # Missing WAHOO_PASSWORD_1P_REF
            "WAHOO_USERNAME": "plain_user@example.com",
            "WAHOO_PASSWORD": "plain_password",
        }

        with patch.dict("os.environ", env_vars, clear=True):
            # Should fall through to plain env vars since 1P refs are incomplete
            username, password = get_credentials()

            assert username == "plain_user@example.com"
            assert password == "plain_password"

    def test_credentials_error_propagates(self) -> None:
        """Test that CredentialsError from 1Password is propagated."""
        error = subprocess.CalledProcessError(1, "op")
        error.stderr = "not signed in"

        env_vars = {
            "WAHOO_USERNAME_1P_REF": "op://vault/wahoo/username",
            "WAHOO_PASSWORD_1P_REF": "op://vault/wahoo/password",
        }

        with (
            patch.dict("os.environ", env_vars, clear=True),
            patch("wahoo_systm_mcp.onepassword.subprocess.run") as mock_run,
        ):
            mock_run.side_effect = error

            with pytest.raises(CredentialsError) as exc_info:
                get_credentials()

            assert "not signed in" in str(exc_info.value)

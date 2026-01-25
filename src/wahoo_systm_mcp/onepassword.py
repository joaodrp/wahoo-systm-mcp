"""1Password integration for retrieving Wahoo SYSTM credentials."""

import os
import subprocess


class CredentialsError(Exception):
    """Raised when credential retrieval fails."""

    pass


def get_credentials_from_1password(username_ref: str, password_ref: str) -> tuple[str, str]:
    """Retrieve credentials from 1Password using secret references.

    Args:
        username_ref: 1Password secret reference for the username
            (e.g., "op://vault/item/username").
        password_ref: 1Password secret reference for the password
            (e.g., "op://vault/item/password").

    Returns:
        A tuple of (username, password).

    Raises:
        CredentialsError: If retrieval from 1Password fails.
    """
    try:
        username_result = subprocess.run(
            ["op", "read", username_ref],
            capture_output=True,
            text=True,
            check=True,
        )
        username = username_result.stdout.strip()

        password_result = subprocess.run(
            ["op", "read", password_ref],
            capture_output=True,
            text=True,
            check=True,
        )
        password = password_result.stdout.strip()

        return username, password
    except FileNotFoundError as e:
        raise CredentialsError(
            "1Password CLI not found. Install the `op` CLI and enable app integration."
        ) from e
    except subprocess.CalledProcessError as e:
        error_message = e.stderr.strip() if e.stderr else str(e)
        raise CredentialsError(
            f"Failed to retrieve credentials from 1Password: {error_message}. "
            "Make sure you're signed in to 1Password and the references are correct."
        ) from e


def get_credentials() -> tuple[str, str]:
    """Get Wahoo SYSTM credentials from 1Password or environment variables.

    Checks for credentials in the following order:
    1. 1Password references via WAHOO_USERNAME_1P_REF and WAHOO_PASSWORD_1P_REF
    2. Plain environment variables WAHOO_USERNAME and WAHOO_PASSWORD

    Returns:
        A tuple of (username, password).

    Raises:
        CredentialsError: If 1Password retrieval fails.
        ValueError: If no credentials are found.
    """
    username_1p_ref = os.environ.get("WAHOO_USERNAME_1P_REF")
    password_1p_ref = os.environ.get("WAHOO_PASSWORD_1P_REF")

    if username_1p_ref and password_1p_ref:
        return get_credentials_from_1password(username_1p_ref, password_1p_ref)

    username = os.environ.get("WAHOO_USERNAME")
    password = os.environ.get("WAHOO_PASSWORD")

    if username and password:
        return username, password

    raise ValueError(
        "No credentials found. Set either WAHOO_USERNAME_1P_REF and "
        "WAHOO_PASSWORD_1P_REF for 1Password integration, or WAHOO_USERNAME "
        "and WAHOO_PASSWORD environment variables."
    )

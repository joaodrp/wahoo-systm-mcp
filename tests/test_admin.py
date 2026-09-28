"""Tests for the admin CLI that manages the Lambda-hosted server's allowlist."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock

import pytest
from botocore.exceptions import ClientError

from wahoo_systm_mcp.remote import admin
from wahoo_systm_mcp.remote.admin import FUNCTION_NAME, Admin
from wahoo_systm_mcp.remote.settings import SettingsError


def client_error(code: str) -> ClientError:
    return ClientError({"Error": {"Code": code, "Message": code}}, "Operation")


class FakeSsm:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.types: dict[str, str] = {}

    def get_parameter(self, *, Name: str, WithDecryption: bool) -> dict[str, Any]:  # noqa: N803
        if Name not in self.values:
            error = client_error("ParameterNotFound")
            raise error
        return {"Parameter": {"Name": Name, "Value": self.values[Name]}}

    def put_parameter(self, *, Name: str, Value: str, Type: str, Overwrite: bool) -> None:  # noqa: N803
        self.values[Name] = Value
        self.types[Name] = Type


class FakeLambda:
    def __init__(self, error: str | None = None) -> None:
        self.error = error
        self.updates: list[dict[str, str]] = []

    def update_function_configuration(self, **kwargs: str) -> None:
        if self.error:
            raise client_error(self.error)
        self.updates.append(kwargs)


@pytest.fixture
def ssm() -> FakeSsm:
    return FakeSsm()


@pytest.fixture
def lambda_client() -> FakeLambda:
    return FakeLambda()


@pytest.fixture
def output() -> list[str]:
    return []


@pytest.fixture
def cli(ssm: FakeSsm, lambda_client: FakeLambda, output: list[str]) -> Admin:
    return Admin(ssm, lambda_client, "/p", out=output.append)  # type: ignore[arg-type]


def allowed(ssm: FakeSsm) -> list[str]:
    return json.loads(ssm.values["/p/ALLOWED_EMAILS"])


class TestAdmin:
    def test_list_empty(self, cli: Admin, output: list[str]) -> None:
        cli.list()
        assert output == ["No emails allowed yet. Add one with: allow <email>"]

    def test_first_allow_creates_secret(
        self, cli: Admin, ssm: FakeSsm, lambda_client: FakeLambda, output: list[str]
    ) -> None:
        cli.allow(["Alice@Example.com"])

        assert allowed(ssm) == ["alice@example.com"]
        assert len(ssm.values["/p/SIGNING_SECRET"]) == 64
        assert set(ssm.types.values()) == {"SecureString"}
        assert lambda_client.updates[0]["FunctionName"] == FUNCTION_NAME
        assert output == [
            "alice@example.com can sign in.",
            f"Recycled {FUNCTION_NAME} so it picks up the change.",
        ]

    def test_allow_keeps_secret_and_others(
        self, cli: Admin, ssm: FakeSsm, output: list[str]
    ) -> None:
        cli.allow(["a@example.com"])
        secret = ssm.values["/p/SIGNING_SECRET"]
        cli.allow(["b@example.com", "a@example.com"])

        assert allowed(ssm) == ["a@example.com", "b@example.com"]
        assert ssm.values["/p/SIGNING_SECRET"] == secret
        assert "a@example.com already can sign in." in output

    def test_allow_rejects_invalid_email(self, cli: Admin, ssm: FakeSsm) -> None:
        with pytest.raises(SettingsError):
            cli.allow(["nope"])
        assert ssm.values == {}

    def test_list(self, cli: Admin, output: list[str]) -> None:
        cli.allow(["b@example.com", "a@example.com"])
        output.clear()
        cli.list()
        assert output == ["a@example.com", "b@example.com"]

    def test_deny(self, cli: Admin, ssm: FakeSsm, output: list[str]) -> None:
        cli.allow(["a@example.com", "b@example.com"])
        cli.deny(["A@example.com"])
        assert allowed(ssm) == ["b@example.com"]
        assert "a@example.com can no longer sign in." in output

    def test_deny_last_leaves_empty_list(self, cli: Admin, ssm: FakeSsm, output: list[str]) -> None:
        cli.allow(["a@example.com"])
        cli.deny(["a@example.com"])
        assert allowed(ssm) == []
        assert "Nobody can sign in now." in output

    def test_deny_unknown(self, cli: Admin) -> None:
        cli.allow(["a@example.com"])
        with pytest.raises(SettingsError, match=r"b@example\.com"):
            cli.deny(["b@example.com"])

    def test_sign_out_all(self, cli: Admin, ssm: FakeSsm) -> None:
        cli.allow(["a@example.com"])
        secret = ssm.values["/p/SIGNING_SECRET"]
        cli.sign_out_all()
        assert ssm.values["/p/SIGNING_SECRET"] != secret

    def test_not_deployed_yet(self, ssm: FakeSsm, output: list[str]) -> None:
        cli = Admin(ssm, FakeLambda("ResourceNotFoundException"), "/p", out=output.append)  # type: ignore[arg-type]
        cli.allow(["a@example.com"])
        assert output[-1] == f"{FUNCTION_NAME} isn't deployed yet; deploy it next."

    def test_other_errors_propagate(self, ssm: FakeSsm) -> None:
        cli = Admin(ssm, FakeLambda("AccessDeniedException"), "/p")  # type: ignore[arg-type]
        with pytest.raises(ClientError):
            cli.allow(["a@example.com"])
        ssm.get_parameter = MagicMock(side_effect=client_error("AccessDeniedException"))  # type: ignore[method-assign]
        with pytest.raises(ClientError):
            cli.list()


class TestMain:
    @pytest.fixture
    def session(self, monkeypatch: pytest.MonkeyPatch, ssm: FakeSsm) -> MagicMock:
        session = MagicMock(region_name="us-west-2")
        session.client.side_effect = lambda name: ssm if name == "ssm" else FakeLambda()
        monkeypatch.setattr(admin.boto3.session, "Session", MagicMock(return_value=session))
        return session

    def test_allow_list_deny(
        self, session: MagicMock, ssm: FakeSsm, capsys: pytest.CaptureFixture[str]
    ) -> None:
        assert admin.main(["allow", "a@example.com", "--prefix", "/p"]) == 0
        assert admin.main(["list", "--prefix", "/p"]) == 0
        assert admin.main(["deny", "a@example.com", "--prefix", "/p"]) == 0
        assert admin.main(["sign-out-all", "--prefix", "/p"]) == 0

        out = capsys.readouterr().out
        assert "Region: us-west-2" in out
        assert "a@example.com\n" in out

    def test_error_exit_code(self, session: MagicMock, capsys: pytest.CaptureFixture[str]) -> None:
        assert admin.main(["deny", "a@example.com", "--prefix", "/p"]) == 1
        assert "Not on the allowlist" in capsys.readouterr().err

    def test_allow_needs_email(self, session: MagicMock) -> None:
        with pytest.raises(SystemExit):
            admin.main(["allow"])

"""AWS Lambda entry point, started by run.sh as `uvicorn --factory ...lambda_app:create_app`.

run.sh runs under the AWS Lambda Web Adapter layer, which turns function URL invocations into
HTTP requests to uvicorn. Settings come from SSM Parameter Store once per cold start, so the
secrets never appear in the function's configuration.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import boto3  # Provided by the Lambda Python runtime; not bundled

from wahoo_systm_mcp.remote.app import create_remote_app
from wahoo_systm_mcp.remote.settings import DEFAULT_SSM_PREFIX, RemoteSettings

if TYPE_CHECKING:
    from fastmcp.server.http import StarletteWithLifespan


def create_app() -> StarletteWithLifespan:
    prefix = os.environ.get("SSM_PREFIX", DEFAULT_SSM_PREFIX)
    settings = RemoteSettings.from_ssm(boto3.client("ssm"), prefix)
    return create_remote_app(settings)

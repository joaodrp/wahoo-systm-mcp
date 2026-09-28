"""Build build/lambda.zip for template.yaml: this package and its dependencies, for Lambda.

Dependencies come from uv.lock as Linux arm64 wheels, so this works on any OS without Docker or
`sam build`. The zip is written here rather than by `sam deploy` so run.sh keeps its executable
bit, which a Windows file system can't record. Entries have fixed timestamps, so an unchanged
build produces an identical zip and `sam deploy` has nothing to upload.

Usage: uv run python scripts/build_lambda.py
"""

from __future__ import annotations

import shutil
import stat
import subprocess
import zipfile
from pathlib import Path

PYTHON_VERSION = "3.13"  # Runtime in template.yaml
# Architectures in template.yaml; Lambda's Amazon Linux 2023 has glibc 2.34
PLATFORM = "aarch64-manylinux_2_28"

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
PACKAGE = BUILD / "lambda"
ZIP_PATH = BUILD / "lambda.zip"

# The function's handler. The Lambda Web Adapter layer (AWS_LAMBDA_EXEC_WRAPPER=/opt/bootstrap)
# runs it, waits for uvicorn to listen, then forwards function URL requests to it. The runtime
# directory provides boto3, which isn't bundled.
RUN_SH = """#!/bin/bash
export PYTHONPATH="$LAMBDA_TASK_ROOT:$LAMBDA_RUNTIME_DIR${PYTHONPATH:+:$PYTHONPATH}"
exec python3 -m uvicorn wahoo_systm_mcp.remote.lambda_app:create_app --factory \\
  --host 127.0.0.1 --port "${AWS_LWA_PORT:-8080}" --no-server-header
"""


def run(*args: str) -> None:
    subprocess.run(args, check=True, cwd=ROOT)


def build_package() -> None:
    shutil.rmtree(BUILD, ignore_errors=True)
    requirements = BUILD / "requirements.txt"
    run(
        "uv", "export", "--frozen", "--no-dev", "--no-emit-project", "--no-hashes",
        "--quiet", "--output-file", str(requirements),
    )  # fmt: skip
    run(
        "uv", "pip", "install", "--quiet", "--target", str(PACKAGE),
        "--python-platform", PLATFORM, "--python-version", PYTHON_VERSION,
        "--only-binary", ":all:", "--requirement", str(requirements),
    )  # fmt: skip
    # This package is pure Python, so unpacking its wheel installs it. (uv would also add a
    # timestamped cache file and console scripts for the build machine.)
    run("uv", "build", "--wheel", "--quiet", "--out-dir", str(BUILD / "dist"))
    (wheel,) = (BUILD / "dist").glob("*.whl")
    with zipfile.ZipFile(wheel) as archive:
        archive.extractall(PACKAGE)

    # Console scripts point at the build machine's Python, and bytecode is rebuilt on Lambda
    shutil.rmtree(PACKAGE / "bin", ignore_errors=True)
    for cache in list(PACKAGE.rglob("__pycache__")):
        shutil.rmtree(cache)
    (PACKAGE / "run.sh").write_bytes(RUN_SH.encode())


def write_zip() -> None:
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(PACKAGE.rglob("*")):
            if not path.is_file():
                continue
            name = path.relative_to(PACKAGE).as_posix()
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            mode = 0o755 if name == "run.sh" else 0o644
            info.external_attr = (stat.S_IFREG | mode) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())


def main() -> None:
    build_package()
    write_zip()
    unzipped = sum(p.stat().st_size for p in PACKAGE.rglob("*") if p.is_file())
    print(  # noqa: T201
        f"Built {ZIP_PATH.relative_to(ROOT)}: {ZIP_PATH.stat().st_size / 1e6:.1f} MB "
        f"({unzipped / 1e6:.1f} MB unzipped; Lambda allows 250 MB)"
    )


if __name__ == "__main__":
    main()

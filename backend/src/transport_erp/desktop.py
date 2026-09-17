from __future__ import annotations

import os
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import uvicorn


def _find_frontend_dir() -> Path:
    configured = os.getenv("TRANSPORT_ERP_FRONTEND_DIR")
    if configured:
        path = Path(configured).expanduser().resolve()
        if (path / "index.html").exists():
            return path

    candidates: list[Path] = []
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root:
        candidates.append(Path(bundle_root) / "frontend")

    source_file = Path(__file__).resolve()
    if len(source_file.parents) >= 4:
        candidates.append(source_file.parents[3] / "frontend" / "out")

    for candidate in candidates:
        if (candidate / "index.html").exists():
            return candidate.resolve()

    raise RuntimeError(
        "Frontend build not found. Run `npm run build` in frontend or set "
        "TRANSPORT_ERP_FRONTEND_DIR."
    )


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_until_ready(url: str, timeout_seconds: float = 15.0) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as response:  # noqa: S310
                if response.status == 200:
                    return
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            time.sleep(0.1)
    raise RuntimeError(f"TransportERP-UA local server did not start: {last_error!r}")


def _check_local_api(base_url: str) -> None:
    with urllib.request.urlopen(f"{base_url}/api/local/status", timeout=5.0) as response:  # noqa: S310
        if response.status != 200:
            raise RuntimeError("TransportERP-UA local status check failed")

    with urllib.request.urlopen(f"{base_url}/", timeout=5.0) as response:  # noqa: S310
        if response.status != 200:
            raise RuntimeError("TransportERP-UA bundled frontend check failed")


def _create_uvicorn_config(application: Any, port: int) -> uvicorn.Config:
    """Create a console-independent Uvicorn configuration for desktop bundles."""
    return uvicorn.Config(
        application,
        host="127.0.0.1",
        port=port,
        log_level="warning",
        access_log=False,
        # PyInstaller --windowed sets sys.stdout/sys.stderr to None on Windows.
        # Uvicorn's default logging formatter calls isatty() on those streams,
        # so desktop bundles must not install the console-oriented log config.
        log_config=None,
    )


def _run_packaged_preflight(frontend_dir: Path) -> None:
    """Validate the frozen runtime without starting GUI/server threads."""
    if not (frontend_dir / "index.html").is_file():
        raise RuntimeError("Bundled frontend index.html is missing")

    from transport_erp.config import get_settings
    from transport_erp.local_runtime import ensure_local_storage

    settings = get_settings()
    ensure_local_storage(settings)
    if not settings.local_database_path.is_file():
        raise RuntimeError("Local SQLite database was not initialized")

    # Import the fully wired FastAPI application after the packaged environment
    # is configured. This validates packaged imports and static frontend mounting.
    from transport_erp.main import app as application

    if application is None:
        raise RuntimeError("FastAPI application was not initialized")

    # Construct the exact Uvicorn configuration used by the real desktop launch.
    # This specifically guards Windows --windowed builds, where stdout/stderr are None.
    _create_uvicorn_config(application, 0)


def main() -> None:
    frontend_dir = _find_frontend_dir()

    os.environ.setdefault("TRANSPORT_ERP_DEPLOYMENT_PROFILE", "local")
    os.environ.setdefault("TRANSPORT_ERP_ENVIRONMENT", "local")
    os.environ["TRANSPORT_ERP_FRONTEND_DIR"] = str(frontend_dir)

    if os.getenv("TRANSPORT_ERP_SMOKE_TEST_ONLY") == "1":
        _run_packaged_preflight(frontend_dir)
        return

    port = _free_port()

    # Import only after the desktop environment is configured so the packaged
    # FastAPI app mounts the bundled static frontend on first initialization.
    from transport_erp.main import app as application

    config = _create_uvicorn_config(application, port)
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, name="transport-erp-local-api", daemon=True)
    thread.start()

    base_url = f"http://127.0.0.1:{port}"
    _wait_until_ready(f"{base_url}/health/live")
    _check_local_api(base_url)

    try:
        import webview
    except ImportError as exc:
        server.should_exit = True
        thread.join(timeout=5.0)
        raise RuntimeError(
            "Desktop runtime is not installed. Install the project with the `desktop` extra."
        ) from exc

    webview.create_window(
        "TransportERP-UA",
        base_url,
        width=1440,
        height=900,
        resizable=True,
    )
    try:
        webview.start()
    finally:
        server.should_exit = True
        thread.join(timeout=5.0)


if __name__ == "__main__":
    main()

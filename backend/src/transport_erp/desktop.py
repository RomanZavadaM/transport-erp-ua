from __future__ import annotations

import os
import socket
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

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
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as response:  # noqa: S310
                if response.status == 200:
                    return
        except (urllib.error.URLError, TimeoutError):
            time.sleep(0.1)
    raise RuntimeError("TransportERP-UA local server did not start")


def _check_local_api(base_url: str) -> None:
    with urllib.request.urlopen(f"{base_url}/api/local/status", timeout=5.0) as response:  # noqa: S310
        if response.status != 200:
            raise RuntimeError("TransportERP-UA local status check failed")

    with urllib.request.urlopen(f"{base_url}/", timeout=5.0) as response:  # noqa: S310
        if response.status != 200:
            raise RuntimeError("TransportERP-UA bundled frontend check failed")


def main() -> None:
    frontend_dir = _find_frontend_dir()
    port = _free_port()

    os.environ.setdefault("TRANSPORT_ERP_DEPLOYMENT_PROFILE", "local")
    os.environ.setdefault("TRANSPORT_ERP_ENVIRONMENT", "local")
    os.environ["TRANSPORT_ERP_FRONTEND_DIR"] = str(frontend_dir)

    # Import only after the desktop environment is configured so the packaged
    # FastAPI app mounts the bundled static frontend on first initialization.
    from transport_erp.main import app as application

    config = uvicorn.Config(
        application,
        host="127.0.0.1",
        port=port,
        log_level="warning",
        access_log=False,
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, name="transport-erp-local-api", daemon=True)
    thread.start()

    base_url = f"http://127.0.0.1:{port}"
    _wait_until_ready(f"{base_url}/health/live")

    if "--smoke-test" in sys.argv[1:]:
        try:
            _check_local_api(base_url)
        finally:
            server.should_exit = True
            thread.join(timeout=5.0)
        return

    try:
        import webview  # type: ignore[import-not-found]
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

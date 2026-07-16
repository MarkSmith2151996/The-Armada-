from __future__ import annotations

import fcntl
import json
import subprocess
import time
import urllib.request
from urllib.parse import quote
from pathlib import Path
from threading import Lock
from typing import Any


class CDPPool:
    BASE_PORT = 9222
    MAX_INSTANCES = 4
    CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    PROFILE_BASE = Path.home() / "chrome-cdp"
    LOCK_BASE = Path("/tmp/armada-cdp-pool")
    READY_TIMEOUT_SECONDS = 10.0
    READY_POLL_SECONDS = 0.25

    def __init__(self) -> None:
        self._lock = Lock()
        self._instances: dict[int, dict[str, Any]] = {}

    def _version_url(self, port: int) -> str:
        return f"http://localhost:{port}/json/version"

    def _list_url(self, port: int) -> str:
        return f"http://localhost:{port}/json"

    def _close_url(self, port: int, tab_id: str) -> str:
        return f"http://localhost:{port}/json/close/{tab_id}"

    def _new_url(self, port: int) -> str:
        return f"http://localhost:{port}/json/new?{quote('about:blank', safe='')}"

    def _is_ready(self, port: int) -> bool:
        try:
            with urllib.request.urlopen(self._version_url(port), timeout=3) as response:
                payload = json.load(response)
            return bool(payload.get("Browser"))
        except Exception:
            return False

    def _process_alive(self, process: subprocess.Popen[Any] | None) -> bool:
        return process is None or process.poll() is None

    def _terminate_process(self, process: subprocess.Popen[Any] | None) -> None:
        if process is None or process.poll() is not None:
            return
        try:
            process.terminate()
            process.wait(timeout=5)
        except Exception:
            try:
                process.kill()
            except Exception:
                pass

    def _wait_until_ready(self, port: int) -> bool:
        import time

        deadline = time.time() + self.READY_TIMEOUT_SECONDS
        while time.time() < deadline:
            if self._is_ready(port):
                return True
            time.sleep(self.READY_POLL_SECONDS)
        return False

    def _launch_chrome(self, port: int) -> subprocess.Popen[Any]:
        profile = self.PROFILE_BASE / str(port)
        profile.mkdir(parents=True, exist_ok=True)
        process = subprocess.Popen(
            [
                self.CHROME_PATH,
                "--headless=new",
                f"--remote-debugging-port={port}",
                f"--user-data-dir={profile}",
                "--remote-allow-origins=*",
                "--disable-gpu",
                "--no-sandbox",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if not self._wait_until_ready(port):
            self._terminate_process(process)
            raise RuntimeError(f"Chrome CDP on port {port} did not become ready")
        return process

    def _next_port(self) -> int | None:
        for port in range(self.BASE_PORT, self.BASE_PORT + self.MAX_INSTANCES):
            if port not in self._instances:
                return port
        return None

    def _acquire_port_lock_unlocked(self, port: int) -> bool:
        info = self._instances[port]
        if info.get("lock_file") is not None:
            return True
        self.LOCK_BASE.mkdir(parents=True, exist_ok=True)
        lock_file = (self.LOCK_BASE / f"{port}.lock").open("a+")
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            lock_file.close()
            return False
        info["lock_file"] = lock_file
        return True

    def _release_port_lock_unlocked(self, port: int) -> None:
        lock_file = self._instances[port].pop("lock_file", None)
        if lock_file is None:
            return
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        finally:
            lock_file.close()

    def _ensure_registered_unlocked(self, port: int) -> None:
        if port in self._instances:
            return
        if self._is_ready(port):
            self._instances[port] = {"status": "free", "foreman": None, "process": None}

    def _ensure_healthy_unlocked(self, port: int) -> dict[str, Any]:
        info = self._instances.get(port)
        if info is None:
            if self._is_ready(port):
                info = {"status": "free", "foreman": None, "process": None}
                self._instances[port] = info
                return info
            process = self._launch_chrome(port)
            info = {"status": "free", "foreman": None, "process": process}
            self._instances[port] = info
            return info

        if self._is_ready(port) and self._process_alive(info.get("process")):
            return info

        self._terminate_process(info.get("process"))
        process = self._launch_chrome(port)
        info["process"] = process
        return info

    def acquire(self, foreman_id: str = "") -> dict[str, Any]:
        with self._lock:
            for port in range(self.BASE_PORT, self.BASE_PORT + self.MAX_INSTANCES):
                self._ensure_registered_unlocked(port)

            for port in sorted(self._instances):
                info = self._instances[port]
                if info["status"] != "free":
                    continue
                if not self._acquire_port_lock_unlocked(port):
                    continue
                try:
                    info = self._ensure_healthy_unlocked(port)
                    info["status"] = "acquired"
                    info["foreman"] = foreman_id
                    return {"port": port, "status": "acquired"}
                except Exception:
                    self._release_port_lock_unlocked(port)
                    raise

            port = self._next_port()
            if port is None:
                return {"error": "All CDP ports are occupied; wait for a worker batch to finish"}

            self._instances[port] = {"status": "free", "foreman": None, "process": None}
            if not self._acquire_port_lock_unlocked(port):
                return {"error": "All CDP ports are occupied; wait for a worker batch to finish"}
            try:
                process = self._launch_chrome(port)
                self._instances[port].update({"status": "acquired", "foreman": foreman_id, "process": process})
                return {"port": port, "status": "acquired"}
            except Exception:
                self._release_port_lock_unlocked(port)
                raise

    def endpoint_for(self, cdp_port: int | None = None) -> tuple[int, str]:
        with self._lock:
            if cdp_port is not None:
                self._ensure_healthy_unlocked(cdp_port)
                return cdp_port, f"http://localhost:{cdp_port}"

            for port in range(self.BASE_PORT, self.BASE_PORT + self.MAX_INSTANCES):
                self._ensure_registered_unlocked(port)

            for port in sorted(self._instances):
                if self._instances[port]["status"] == "free":
                    self._ensure_healthy_unlocked(port)
                    return port, f"http://localhost:{port}"

            if self._instances:
                port = sorted(self._instances)[0]
                self._ensure_healthy_unlocked(port)
                return port, f"http://localhost:{port}"

            port = self.BASE_PORT
            self._ensure_healthy_unlocked(port)
            return port, f"http://localhost:{port}"

    def cleanup(self, cdp_port: int) -> dict[str, Any]:
        try:
            with urllib.request.urlopen(self._list_url(cdp_port), timeout=5) as response:
                tabs = json.load(response)
            request = urllib.request.Request(self._new_url(cdp_port), method="PUT")
            with urllib.request.urlopen(request, timeout=5) as response:
                blank_tab = json.load(response)
            blank_tab_id = blank_tab.get("id", "")
            if not blank_tab_id:
                raise RuntimeError("Chrome did not return an about:blank tab")
            closed = 0
            for tab in tabs:
                if tab.get("type") != "page":
                    continue
                tab_id = tab.get("id", "")
                if not tab_id or tab_id == blank_tab_id:
                    continue
                try:
                    urllib.request.urlopen(self._close_url(cdp_port, tab_id), timeout=3).read()
                    closed += 1
                except Exception:
                    pass
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline:
                with urllib.request.urlopen(self._list_url(cdp_port), timeout=3) as response:
                    remaining = json.load(response)
                page_ids = {tab.get("id") for tab in remaining if tab.get("type") == "page"}
                if page_ids == {blank_tab_id}:
                    break
                time.sleep(0.1)
            return {"success": True, "tabs_closed": closed}
        except Exception as exc:
            return {"success": False, "tabs_closed": 0, "error": str(exc)}

    def release(self, cdp_port: int) -> dict[str, Any]:
        with self._lock:
            if cdp_port not in self._instances:
                return {"error": f"Port {cdp_port} is not managed by this pool"}
            if self._instances[cdp_port].get("lock_file") is None:
                return {"error": f"Port {cdp_port} is not acquired by this MCP process"}
            self._instances[cdp_port]["status"] = "free"
            self._instances[cdp_port]["foreman"] = None
            self._release_port_lock_unlocked(cdp_port)
            return {"port": cdp_port, "status": "released"}

    def status(self) -> dict[str, Any]:
        with self._lock:
            return {
                "instances": {
                    port: {"status": info["status"], "foreman": info["foreman"]}
                    for port, info in sorted(self._instances.items())
                },
                "total": len(self._instances),
                "free": sum(1 for info in self._instances.values() if info["status"] == "free"),
                "acquired": sum(1 for info in self._instances.values() if info["status"] == "acquired"),
            }

    def register_existing(self, port: int) -> None:
        with self._lock:
            self._ensure_registered_unlocked(port)


pool = CDPPool()
_initialized = False
_init_lock = Lock()


def ensure_initialized() -> None:
    global _initialized
    if _initialized:
        return
    with _init_lock:
        if _initialized:
            return
        import time

        time.sleep(1)
        for port in range(CDPPool.BASE_PORT, CDPPool.BASE_PORT + CDPPool.MAX_INSTANCES):
            pool.register_existing(port)
        _initialized = True

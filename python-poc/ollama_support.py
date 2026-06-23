from __future__ import annotations

import os
import shutil
import socket
import subprocess
from dataclasses import dataclass
from typing import Any, Dict
from urllib.parse import urlparse


DEFAULT_OLLAMA_HOST = "http://127.0.0.1:11434"


@dataclass
class OllamaProbe:
    binary_path: str | None
    host: str
    hostname: str
    port: int
    connect_ok: bool
    connect_error: str | None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "binary_path": self.binary_path,
            "host": self.host,
            "hostname": self.hostname,
            "port": self.port,
            "connect_ok": self.connect_ok,
            "connect_error": self.connect_error,
        }


def resolve_ollama_host() -> str:
    return os.environ.get("OLLAMA_HOST", DEFAULT_OLLAMA_HOST)


def probe_ollama_host(timeout_seconds: float = 1.0) -> OllamaProbe:
    host = resolve_ollama_host()
    parsed = urlparse(host if "://" in host else f"http://{host}")
    hostname = parsed.hostname or "127.0.0.1"
    port = parsed.port or 11434
    binary_path = shutil.which("ollama")

    try:
        with socket.create_connection((hostname, port), timeout=timeout_seconds):
            connect_ok = True
            connect_error = None
    except OSError as exc:
        connect_ok = False
        connect_error = f"{exc.__class__.__name__}: {exc}"

    return OllamaProbe(
        binary_path=binary_path,
        host=host,
        hostname=hostname,
        port=port,
        connect_ok=connect_ok,
        connect_error=connect_error,
    )


def format_ollama_diagnostics() -> str:
    probe = probe_ollama_host()
    return (
        "ollama diagnostics: "
        f"binary_path={probe.binary_path!r} "
        f"host={probe.host!r} "
        f"hostname={probe.hostname!r} "
        f"port={probe.port} "
        f"connect_ok={probe.connect_ok} "
        f"connect_error={probe.connect_error!r}"
    )


def run_ollama(model: str, prompt: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["ollama", "run", model],
        input=prompt,
        text=True,
        capture_output=True,
        check=False,
    )

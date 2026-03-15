from __future__ import annotations

import argparse
import concurrent.futures
import contextlib
import hashlib
import http.server
import os
import pathlib
import random
import shutil
import socketserver
import tempfile
import threading
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass


def getenv_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return int(value)


def getenv_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return float(value)


@dataclass(frozen=True)
class Config:
    role: str = os.getenv("INCIDENT_ROLE", "simulator")
    profile: str = os.getenv("INCIDENT_PROFILE", "cpu_periodic")
    name: str = os.getenv("INCIDENT_NAME", "incident-lab")
    target_url: str = os.getenv("TARGET_URL", "http://incident-sink:8080/blob?size_kb=16")
    tick_seconds: float = getenv_float("TICK_SECONDS", 1.0)
    port: int = getenv_int("PORT", 8080)
    cpu_burst_seconds: int = getenv_int("CPU_BURST_SECONDS", 12)
    cpu_idle_seconds: int = getenv_int("CPU_IDLE_SECONDS", 25)
    memory_block_mb: int = getenv_int("MEMORY_BLOCK_MB", 96)
    memory_hold_seconds: int = getenv_int("MEMORY_HOLD_SECONDS", 15)
    burst_concurrency: int = getenv_int("BURST_CONCURRENCY", 12)
    burst_requests: int = getenv_int("BURST_REQUESTS", 12)
    beacon_interval_seconds: int = getenv_int("BEACON_INTERVAL_SECONDS", 20)
    stage_dir: str = os.getenv("STAGE_DIR", "/tmp/incident-lab")
    stage_file_mb: int = getenv_int("STAGE_FILE_MB", 8)
    once: bool = os.getenv("INCIDENT_ONCE", "0") == "1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Safe incident simulation lab")
    parser.add_argument("--role", choices=["simulator", "sink"], default=os.getenv("INCIDENT_ROLE", "simulator"))
    return parser.parse_args()


class BlobHandler(http.server.BaseHTTPRequestHandler):
    server_version = "IncidentLabSink/0.1"

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/healthz":
            body = b"ok\n"
        elif parsed.path == "/blob":
            params = urllib.parse.parse_qs(parsed.query)
            size_kb = int(params.get("size_kb", ["16"])[0])
            body = (b"A" * 1024) * max(size_kb, 1)
        else:
            body = b"incident-lab-sink\n"
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"[sink] {self.address_string()} - {fmt % args}")


class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


def run_sink(cfg: Config) -> int:
    with ThreadingHTTPServer(("0.0.0.0", cfg.port), BlobHandler) as server:
        print(f"[sink] listening on 0.0.0.0:{cfg.port}")
        server.serve_forever()
    return 0


def busy_cpu(seconds: int) -> None:
    deadline = time.monotonic() + max(seconds, 1)
    value = 0
    while time.monotonic() < deadline:
        digest = hashlib.sha256(f"{value}".encode()).digest()
        value ^= digest[0]


def allocate_memory(block_mb: int, hold_seconds: int) -> None:
    block = bytearray(block_mb * 1024 * 1024)
    for i in range(0, len(block), 4096):
        block[i] = (i // 4096) % 251
    time.sleep(max(hold_seconds, 1))


def http_get(url: str) -> None:
    with contextlib.closing(urllib.request.urlopen(url, timeout=10)) as resp:
        while resp.read(64 * 1024):
            pass


def beacon(url: str) -> None:
    try:
        http_get(url)
    except Exception as exc:  # noqa: BLE001
        print(f"[sim] beacon error: {exc}")


def exfil_burst(url: str, concurrency: int, requests: int) -> None:
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=max(concurrency, 1)) as pool:
            list(pool.map(lambda _: http_get(url), range(max(requests, 1))))
    except Exception as exc:  # noqa: BLE001
        print(f"[sim] burst error: {exc}")


def io_stage(stage_dir: str, file_mb: int, hold_seconds: int) -> None:
    root = pathlib.Path(stage_dir)
    root.mkdir(parents=True, exist_ok=True)
    work = pathlib.Path(tempfile.mkdtemp(prefix="incident-lab-", dir=str(root)))
    try:
        data = os.urandom(1024 * 1024)
        for i in range(max(file_mb, 1)):
            with open(work / f"chunk-{i:03d}.bin", "wb") as fh:
                fh.write(data)
        time.sleep(max(hold_seconds, 1))
    finally:
        shutil.rmtree(work, ignore_errors=True)


def run_cpu_periodic(cfg: Config) -> None:
    while True:
        print(f"[sim:{cfg.name}] cpu burst")
        busy_cpu(cfg.cpu_burst_seconds)
        if cfg.once:
            return
        time.sleep(cfg.cpu_idle_seconds)


def run_memory_random(cfg: Config) -> None:
    while True:
        sleep_for = random.randint(8, 30)
        time.sleep(sleep_for)
        block_mb = random.randint(max(cfg.memory_block_mb // 2, 8), max(cfg.memory_block_mb, 8))
        hold_for = random.randint(max(cfg.memory_hold_seconds // 2, 3), max(cfg.memory_hold_seconds, 3))
        print(f"[sim:{cfg.name}] memory allocate {block_mb}MB for {hold_for}s")
        allocate_memory(block_mb, hold_for)
        if cfg.once:
            return


def run_beacon_periodic(cfg: Config) -> None:
    while True:
        print(f"[sim:{cfg.name}] beacon -> {cfg.target_url}")
        beacon(cfg.target_url)
        if cfg.once:
            return
        time.sleep(cfg.beacon_interval_seconds)


def run_exfil_burst(cfg: Config) -> None:
    while True:
        sleep_for = random.randint(20, 45)
        time.sleep(sleep_for)
        print(f"[sim:{cfg.name}] exfil burst -> {cfg.target_url}")
        exfil_burst(cfg.target_url, cfg.burst_concurrency, cfg.burst_requests)
        if cfg.once:
            return


def run_io_staging(cfg: Config) -> None:
    while True:
        sleep_for = random.randint(10, 30)
        time.sleep(sleep_for)
        print(f"[sim:{cfg.name}] io stage in {cfg.stage_dir}")
        io_stage(cfg.stage_dir, cfg.stage_file_mb, cfg.memory_hold_seconds)
        if cfg.once:
            return


def run_mixed_intrusion(cfg: Config) -> None:
    while True:
        print(f"[sim:{cfg.name}] phase 1 beacon")
        beacon(cfg.target_url)
        time.sleep(3)
        print(f"[sim:{cfg.name}] phase 2 cpu")
        busy_cpu(max(cfg.cpu_burst_seconds // 2, 3))
        print(f"[sim:{cfg.name}] phase 3 memory")
        allocate_memory(max(cfg.memory_block_mb // 2, 16), max(cfg.memory_hold_seconds // 2, 3))
        print(f"[sim:{cfg.name}] phase 4 io")
        io_stage(cfg.stage_dir, max(cfg.stage_file_mb // 2, 2), max(cfg.memory_hold_seconds // 3, 2))
        print(f"[sim:{cfg.name}] phase 5 burst")
        exfil_burst(cfg.target_url, max(cfg.burst_concurrency // 2, 4), max(cfg.burst_requests // 2, 4))
        if cfg.once:
            return
        time.sleep(random.randint(20, 40))


PROFILE_RUNNERS = {
    "cpu_periodic": run_cpu_periodic,
    "memory_random": run_memory_random,
    "beacon_periodic": run_beacon_periodic,
    "exfil_burst": run_exfil_burst,
    "io_staging": run_io_staging,
    "mixed_intrusion": run_mixed_intrusion,
}


def run_simulator(cfg: Config) -> int:
    runner = PROFILE_RUNNERS.get(cfg.profile)
    if runner is None:
        raise SystemExit(f"unknown INCIDENT_PROFILE: {cfg.profile}")
    print(f"[sim:{cfg.name}] starting profile={cfg.profile} target={cfg.target_url}")
    runner(cfg)
    return 0


def main() -> int:
    args = parse_args()
    cfg = Config(role=args.role)
    if cfg.role == "sink":
        return run_sink(cfg)
    return run_simulator(cfg)

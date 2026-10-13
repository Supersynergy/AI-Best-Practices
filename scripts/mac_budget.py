#!/usr/bin/env python3
"""Cooperative admission for future heavy jobs. Python 3.12+, no dependencies."""

import argparse
from contextlib import contextmanager
from dataclasses import dataclass
import fcntl
import json
import math
import os
from pathlib import Path
import signal
import stat
import subprocess
import sys
import tempfile
import time
import uuid

GIB = 1024**3


@dataclass(frozen=True)
class Limits:
    memory_bytes: int
    io_slots: int
    headroom_bytes: int
    disk_headroom_bytes: int
    live_guard: bool = True


def pid_birth(pid):
    if sys.platform.startswith("linux"):
        try:
            return Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()[19]
        except (OSError, IndexError):
            return None
    result = subprocess.run(
        ["ps", "-p", str(pid), "-o", "lstart="],
        capture_output=True,
        text=True,
        timeout=3,
    )
    return result.stdout.strip() or None


def physical_memory():
    if sys.platform == "darwin":
        return int(subprocess.check_output(["sysctl", "-n", "hw.memsize"], timeout=3))
    return os.sysconf("SC_PHYS_PAGES") * os.sysconf("SC_PAGE_SIZE")


def live_probe():
    if sys.platform == "darwin":
        import re

        pressure = int(
            subprocess.check_output(
                ["sysctl", "-n", "kern.memorystatus_vm_pressure_level"], timeout=3
            )
        )
        vm = subprocess.check_output(["vm_stat"], text=True, timeout=3)
        size = int(re.search(r"page size of (\d+)", vm).group(1))
        pages = {k: int(v) for k, v in re.findall(r"^([^:\n]+):\s+(\d+)\.", vm, re.M)}
        # Reclaimability is an estimate; pressure is the separate admission gate.
        available = (
            sum(
                pages.get(k, 0)
                for k in ("Pages free", "Pages inactive", "Pages speculative")
            )
            * size
        )
        return {"pressure": pressure, "available_bytes": available}
    mem = dict(
        line.split(":", 1) for line in Path("/proc/meminfo").read_text().splitlines()
    )
    return {
        "pressure": 1,
        "available_bytes": int(mem["MemAvailable"].split()[0]) * 1024,
    }


def group_alive(pgid):
    result = subprocess.run(
        ["ps", "-axo", "pgid=,stat="],
        capture_output=True,
        text=True,
        timeout=3,
        check=True,
    )
    return any(
        int(parts[0]) == pgid and not parts[1].startswith("Z")
        for line in result.stdout.splitlines()
        if len(parts := line.split()) == 2
    )


class Budget:
    def __init__(self, directory, limits):
        self.directory = Path(directory).expanduser()
        self.limits = limits
        if self.directory.is_symlink():
            raise ValueError("state directory must not be a symlink")
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        metadata = self.directory.stat()
        if metadata.st_uid != os.getuid() or metadata.st_mode & 0o022:
            raise ValueError(
                "state directory must be owned by the current user and not writable by others"
            )
        self.file = self.directory / "leases.json"
        self.birth = pid_birth(os.getpid())
        self.cached_probe = None
        self.probed_at = 0

    @contextmanager
    def locked(self):
        lock = self.directory / "lock"
        descriptor = os.open(lock, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        deadline = time.monotonic() + 3
        try:
            metadata = os.fstat(descriptor)
            if metadata.st_uid != os.getuid() or not stat.S_ISREG(metadata.st_mode):
                raise ValueError("invalid lock ownership or type")
            while True:
                try:
                    fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        raise TimeoutError("registry lock deadline exceeded")
                    time.sleep(0.02)
            yield
        finally:
            os.close(descriptor)

    def read(self):
        try:
            descriptor = os.open(self.file, os.O_RDONLY | os.O_NOFOLLOW)
        except FileNotFoundError:
            return []
        except OSError as error:
            raise ValueError("invalid registry path") from error
        with os.fdopen(descriptor) as stream:
            metadata = os.fstat(stream.fileno())
            if metadata.st_uid != os.getuid() or not stat.S_ISREG(metadata.st_mode):
                raise ValueError("invalid registry ownership or type")
            raw = stream.read(128 * 1024 + 1)
        if len(raw) > 128 * 1024:
            raise ValueError("registry exceeded 128 KiB")
        try:
            records = json.loads(raw)
            if not isinstance(records, list) or len(records) > 128:
                raise ValueError("invalid registry structure")
            for item in records:
                if (
                    not isinstance(item, dict)
                    or not isinstance(item.get("token"), str)
                    or not isinstance(item.get("birth"), str)
                ):
                    raise ValueError("invalid lease identity")
                for field in ("pid", "memory_bytes", "io_slots"):
                    if type(item.get(field)) is not int or item[field] < 0:
                        raise ValueError("invalid lease resource value")
            return records
        except (ValueError, TypeError) as error:
            raise ValueError("malformed registry; left untouched") from error

    def write(self, records):
        descriptor, name = tempfile.mkstemp(prefix=".leases-", dir=self.directory)
        try:
            with os.fdopen(descriptor, "w") as stream:
                json.dump(records, stream, separators=(",", ":"))
                stream.write("\n")
            os.replace(name, self.file)
        finally:
            if os.path.exists(name):
                os.unlink(name)

    @staticmethod
    def active(records):
        return [
            r
            for r in records
            if pid_birth(r["pid"]) == r["birth"]
            or (r.get("pgid") and group_alive(r["pgid"]))
        ]

    def attach_group(self, token, pgid):
        with self.locked():
            records = self.read()
            for record in records:
                if (
                    record["token"] == token
                    and record["pid"] == os.getpid()
                    and record["birth"] == self.birth
                ):
                    record["pgid"] = pgid
                    self.write(records)
                    return
            raise RuntimeError("reservation disappeared before child registration")

    def acquire(self, memory_bytes, io_slots):
        if (
            type(memory_bytes) is not int
            or type(io_slots) is not int
            or memory_bytes <= 0
            or io_slots < 0
        ):
            raise ValueError("request needs positive memory and nonnegative I/O slots")
        if memory_bytes > self.limits.memory_bytes or io_slots > self.limits.io_slots:
            raise ValueError("request exceeds the configured total budget")
        if self.birth is None:
            raise RuntimeError("cannot identify the reservation owner")
        if self.limits.live_guard:
            if time.monotonic() - self.probed_at >= 1 or self.cached_probe is None:
                self.cached_probe = live_probe()
                self.probed_at = time.monotonic()
            if (
                self.cached_probe["pressure"] != 1
                or self.cached_probe["available_bytes"]
                < memory_bytes + self.limits.headroom_bytes
            ):
                return None
            space = os.statvfs(self.directory)
            if space.f_bavail * space.f_frsize < self.limits.disk_headroom_bytes:
                return None
        with self.locked():
            records = self.active(self.read())
            if (
                sum(r["memory_bytes"] for r in records) + memory_bytes
                > self.limits.memory_bytes
            ):
                return None
            if sum(r["io_slots"] for r in records) + io_slots > self.limits.io_slots:
                return None
            token = uuid.uuid4().hex
            records.append(
                {
                    "token": token,
                    "pid": os.getpid(),
                    "birth": self.birth,
                    "memory_bytes": memory_bytes,
                    "io_slots": io_slots,
                }
            )
            self.write(records)
            return token

    def wait_for(self, memory_bytes, io_slots, timeout):
        deadline = time.monotonic() + timeout
        notified = False
        while True:
            token = self.acquire(memory_bytes, io_slots)
            if token:
                return token
            if time.monotonic() >= deadline:
                raise TimeoutError("admission deadline exceeded; child was not started")
            if not notified:
                print(
                    "mac-resource-run: waiting for shared RAM/I/O budget",
                    file=sys.stderr,
                )
                notified = True
            time.sleep(min(0.2, max(0, deadline - time.monotonic())))

    def release(self, token):
        with self.locked():
            records = self.read()
            remaining = [
                r
                for r in records
                if not (
                    r["token"] == token
                    and r["pid"] == os.getpid()
                    and r["birth"] == self.birth
                )
            ]
            if remaining != records:
                self.write(remaining)

    def status(self):
        with self.locked():
            records = self.read()
            active = self.active(records)
            if active != records:
                self.write(active)
        return {
            "memory_budget_bytes": self.limits.memory_bytes,
            "io_budget": self.limits.io_slots,
            "reserved_memory_bytes": sum(r["memory_bytes"] for r in active),
            "reserved_io_slots": sum(r["io_slots"] for r in active),
            "leases": active,
        }

    def inherits(self, token, memory_bytes, io_slots):
        if not token:
            return False
        ancestors = set()
        pid = os.getppid()
        for _ in range(32):
            if pid <= 1 or pid in ancestors:
                break
            ancestors.add(pid)
            text = subprocess.check_output(
                ["ps", "-p", str(pid), "-o", "ppid="], text=True, timeout=3
            ).strip()
            if not text:
                break
            pid = int(text)
        with self.locked():
            for record in self.read():
                if (
                    record["token"] == token
                    and record["pid"] in ancestors
                    and pid_birth(record["pid"]) == record["birth"]
                ):
                    if (
                        memory_bytes > record["memory_bytes"]
                        or io_slots > record["io_slots"]
                    ):
                        raise ValueError(
                            "nested request exceeds its parent tree reservation"
                        )
                    return True
            return False


def number(value, name, minimum=0):
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value < minimum
    ):
        raise ValueError(f"{name} must be finite and at least {minimum}")
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--state-dir",
        default=os.environ.get(
            "MAC_RESOURCE_STATE_DIR",
            str(Path.home() / "Library/Caches/ai-best-practices/budget"),
        ),
    )
    parser.add_argument(
        "--config",
        default=os.environ.get(
            "MAC_RESOURCE_CONFIG",
            str(Path.home() / ".config/mac-workflow/resource-budget.json"),
        ),
    )
    commands = parser.add_subparsers(dest="action", required=True)
    commands.add_parser("status")
    command = commands.add_parser("run")
    command.add_argument(
        "--memory-gib",
        type=float,
        default=float(os.environ.get("MAC_RESOURCE_JOB_GIB", "4")),
    )
    command.add_argument(
        "--io-slots",
        type=int,
        default=int(os.environ.get("MAC_RESOURCE_IO_SLOTS", "1")),
    )
    command.add_argument("--wait-seconds", type=float, default=300)
    command.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    config_path = Path(args.config).expanduser()
    config = json.loads(config_path.read_text()) if config_path.exists() else {}
    if not isinstance(config, dict):
        raise ValueError("configuration must be a JSON object")
    memory = physical_memory()
    cap = int(
        number(
            config.get("memory_budget_gib", memory / GIB * 0.5),
            "memory_budget_gib",
            0.01,
        )
        * GIB
    )
    io_slots = config.get("io_slots", 1)
    if type(io_slots) is not int or io_slots < 1:
        raise ValueError("io_slots must be a positive integer")
    guard = config.get("live_guard", True)
    if type(guard) is not bool:
        raise ValueError("live_guard must be boolean")
    limits = Limits(
        cap,
        io_slots,
        int(
            number(
                config.get("headroom_gib", max(2, memory / GIB * 0.1875)),
                "headroom_gib",
            )
            * GIB
        ),
        int(number(config.get("disk_headroom_gib", 20), "disk_headroom_gib") * GIB),
        guard,
    )
    budget = Budget(args.state_dir, limits)
    if args.action == "status":
        print(json.dumps(budget.status(), indent=2))
        return 0
    child_command = (
        args.command[1:] if args.command and args.command[0] == "--" else args.command
    )
    if not child_command:
        raise ValueError("run requires a command after --")
    request = int(number(args.memory_gib, "memory-gib", 0.01) * GIB)
    timeout = number(args.wait_seconds, "wait-seconds", 0)
    if args.io_slots < 0:
        raise ValueError("io-slots must be nonnegative")
    inherited = budget.inherits(
        os.environ.get("MAC_RESOURCE_LEASE"), request, args.io_slots
    )
    token = None if inherited else budget.wait_for(request, args.io_slots, timeout)
    environment = os.environ.copy()
    if token:
        environment["MAC_RESOURCE_LEASE"] = token
    child = None
    try:
        child = subprocess.Popen(child_command, env=environment, start_new_session=True)
        if token:
            budget.attach_group(token, child.pid)

        def forward(signum, _frame):
            try:
                os.killpg(child.pid, signum)
            except ProcessLookupError:
                return

        old_handlers = {
            sig: signal.signal(sig, forward) for sig in (signal.SIGINT, signal.SIGTERM)
        }
        try:
            result = child.wait()
            while group_alive(child.pid):
                time.sleep(0.2)
        finally:
            for sig, handler in old_handlers.items():
                signal.signal(sig, handler)
        return result if result >= 0 else 128 - result
    finally:
        if token:
            if child is None or not group_alive(child.pid):
                budget.release(token)
            else:
                print(
                    "mac-resource-run: child group remains active; reservation retained",
                    file=sys.stderr,
                )


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, RuntimeError, OSError, subprocess.SubprocessError) as error:
        print(f"mac-resource-run: {error}", file=sys.stderr)
        raise SystemExit(2)
    except KeyboardInterrupt:
        print("mac-resource-run: interrupted", file=sys.stderr)
        raise SystemExit(130)

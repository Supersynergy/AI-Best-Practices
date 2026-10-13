#!/usr/bin/env python3
"""Bounded comparison of three owned foreground jobs; writes 18 MiB at 3 samples."""

import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import time

RUNNER = Path(__file__).with_name("mac_budget.py")
WORKER = """import hashlib,json,os,resource,sys,time
from pathlib import Path
root=Path(sys.argv[1]); index=int(sys.argv[2]); start=time.monotonic()
memory=bytearray(32*1024*1024)
for position in range(0,len(memory),4096): memory[position]=1
(root/f"event-{index}.json").write_text(json.dumps({"pid":os.getpid(),"start":start}))
payload=bytes([index])*32768
with (root/f"payload-{index}.bin").open("wb") as stream:
 for _ in range(32): stream.write(payload); time.sleep(.012)
 stream.flush(); os.fsync(stream.fileno())
time.sleep(.12)
end=time.monotonic()
(root/f"event-{index}.json").write_text(json.dumps({"pid":os.getpid(),"start":start,"end":end}))
print(json.dumps({"index":index,"sha256":hashlib.sha256((root/f"payload-{index}.bin").read_bytes()).hexdigest(),"bytes":32768*32}))
"""

libproc = ctypes.CDLL("/usr/lib/libproc.dylib") if sys.platform == "darwin" else None
if libproc:
    libproc.proc_pid_rusage.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_void_p]
    libproc.proc_pid_rusage.restype = ctypes.c_int


def footprint(pid):
    if libproc:
        import struct

        buffer = ctypes.create_string_buffer(296)
        if libproc.proc_pid_rusage(pid, 4, ctypes.byref(buffer)) == 0:
            return struct.unpack_from("Q", buffer.raw, 72)[0]
        return 0
    try:
        for line in Path(f"/proc/{pid}/status").read_text().splitlines():
            if line.startswith("VmRSS:"):
                return int(line.split()[1]) * 1024
    except FileNotFoundError:
        return 0
    return 0


def arm(root, budgeted):
    root.mkdir()
    config = root / "config.json"
    config.write_text(
        json.dumps(
            {
                "memory_budget_gib": 2,
                "io_slots": 1,
                "headroom_gib": 0,
                "disk_headroom_gib": 0,
                "live_guard": True,
            }
        )
    )
    processes = []
    start = time.monotonic()
    for index in range(3):
        command = [sys.executable, "-c", WORKER, str(root), str(index)]
        if budgeted:
            command = [
                sys.executable,
                str(RUNNER),
                "--state-dir",
                str(root / "budget"),
                "--config",
                str(config),
                "run",
                "--memory-gib",
                "0.1",
                "--wait-seconds",
                "10",
                "--",
                *command,
            ]
        processes.append(
            subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
            )
        )
    peak_bytes = 0
    observed = {}
    while any(process.poll() is None for process in processes):
        for path in root.glob("event-*.json"):
            try:
                observed[path.name] = json.loads(path.read_text())
            except json.JSONDecodeError:
                continue
        pids = {p.pid for p in processes if p.poll() is None} | {
            r["pid"] for r in observed.values()
        }
        peak_bytes = max(peak_bytes, sum(footprint(pid) for pid in pids))
        if time.monotonic() - start > 15:
            raise TimeoutError("benchmark deadline exceeded")
        time.sleep(0.025)
    results = []
    for process in processes:
        out, err = process.communicate()
        assert process.returncode == 0, (process.returncode, err)
        results.append(json.loads(out))
    events = [json.loads(path.read_text()) for path in root.glob("event-*.json")]
    points = sorted(
        [(r["start"], 1) for r in events] + [(r["end"], -1) for r in events]
    )
    count = peak = 0
    for _, change in points:
        count += change
        peak = max(peak, count)
    return {
        "wall_seconds": time.monotonic() - start,
        "peak_owned_process_bytes": peak_bytes,
        "peak_active_workers": peak,
        "logical_payload_bytes": sum(r["bytes"] for r in results),
        "results": sorted(results, key=lambda r: r["index"]),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=3)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not 1 <= args.samples <= 5:
        parser.error("samples must be 1..5")
    rows = {"before": [], "after": []}
    source_hash = hashlib.sha256(RUNNER.read_bytes()).hexdigest()
    with tempfile.TemporaryDirectory(prefix="ai-budget-benchmark-") as directory:
        root = Path(directory)
        for index in range(args.samples):
            for key in ("before", "after") if index % 2 == 0 else ("after", "before"):
                result = arm(root / f"{key}-{index}", key == "after")
                assert result["peak_active_workers"] == (3 if key == "before" else 1)
                if rows["before"]:
                    assert result["results"] == rows["before"][0]["results"]
                rows[key].append(result)
    assert hashlib.sha256(RUNNER.read_bytes()).hexdigest() == source_hash, (
        "runner changed during measurement"
    )
    report = {
        "runner_sha256": source_hash,
        "workload": "Three owned jobs, 32 MiB touched memory each, 1 MiB durable payload each, identical output hashes",
        "samples_per_arm": args.samples,
        "host": "macOS" if sys.platform == "darwin" else "Linux",
        "memory_metric": "sum of per-process physical footprint, including waiting wrappers"
        if libproc
        else "sum of per-process RSS",
        "filesystem_cache": "uncontrolled/warm; fresh processes each time",
        "arms": rows,
        "summary": {
            key: {
                field: statistics.median(row[field] for row in values)
                for field in (
                    "wall_seconds",
                    "peak_owned_process_bytes",
                    "peak_active_workers",
                    "logical_payload_bytes",
                )
            }
            for key, values in rows.items()
        },
        "acceptance": "PASS; identical durable payloads; budgeted maximum concurrency = 1",
        "limits": [
            "Synthetic bounded workload, not an application benchmark.",
            "Total payload bytes are unchanged.",
            "Host/NAND writes and SSD life are not measured by payload length.",
            "Foreign jobs were not stopped or modified.",
        ],
    }
    if args.output:
        args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: report[k]
                for k in ("acceptance", "summary", "memory_metric", "limits")
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

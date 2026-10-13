import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import mac_budget


class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.limits = mac_budget.Limits(8 * mac_budget.GIB, 1, 0, 0, False)
        self.budget = mac_budget.Budget(self.root, self.limits)

    def tearDown(self):
        self.tmp.cleanup()

    def test_shared_io_queue_and_release(self):
        first = self.budget.acquire(2 * mac_budget.GIB, 1)
        self.assertIsNotNone(first)
        self.assertIsNone(self.budget.acquire(2 * mac_budget.GIB, 1))
        self.budget.release(first)
        self.assertIsNotNone(self.budget.acquire(2 * mac_budget.GIB, 1))

    def test_process_identity_is_independent_of_caller_timezone(self):
        with patch.dict(os.environ, {"TZ": "UTC"}):
            utc = mac_budget.pid_birth(os.getpid())
        with patch.dict(os.environ, {"TZ": "Pacific/Honolulu"}):
            honolulu = mac_budget.pid_birth(os.getpid())
        self.assertEqual(utc, honolulu)

    def test_shared_memory_queue(self):
        self.assertIsNotNone(self.budget.acquire(6 * mac_budget.GIB, 0))
        self.assertIsNone(self.budget.acquire(3 * mac_budget.GIB, 0))

    def test_oversized_request_is_rejected(self):
        with self.assertRaises(ValueError):
            self.budget.acquire(9 * mac_budget.GIB, 0)

    def test_pressure_blocks_new_work_without_removing_active_lease(self):
        first = self.budget.acquire(mac_budget.GIB, 0)
        guarded = mac_budget.Budget(
            self.root, mac_budget.Limits(8 * mac_budget.GIB, 1, 0, 0, True)
        )
        with patch.object(
            mac_budget,
            "live_probe",
            return_value={"pressure": 2, "available_bytes": 20 * mac_budget.GIB},
        ):
            self.assertIsNone(guarded.acquire(mac_budget.GIB, 0))
        self.assertEqual(len(self.budget.status()["leases"]), 1)
        self.budget.release(first)

    def test_missing_live_probe_fails_closed(self):
        guarded = mac_budget.Budget(
            self.root, mac_budget.Limits(8 * mac_budget.GIB, 1, 0, 0, True)
        )
        with patch.object(
            mac_budget, "live_probe", side_effect=RuntimeError("probe unavailable")
        ):
            with self.assertRaises(RuntimeError):
                guarded.acquire(mac_budget.GIB, 0)

    def test_dead_or_reused_pid_lease_is_recovered(self):
        first = self.budget.acquire(8 * mac_budget.GIB, 1)
        with patch.object(mac_budget, "pid_birth", return_value="different-start"):
            second = self.budget.acquire(mac_budget.GIB, 1)
        self.assertIsNotNone(second)
        self.assertNotEqual(first, second)

    def test_malformed_registry_is_not_overwritten(self):
        self.root.mkdir(exist_ok=True)
        path = self.root / "leases.json"
        path.write_text("{broken")
        with self.assertRaises(ValueError):
            self.budget.status()
        self.assertEqual(path.read_text(), "{broken")

    def test_owner_crash_does_not_free_live_process_group(self):
        token = self.budget.acquire(8 * mac_budget.GIB, 1)
        self.budget.attach_group(token, 999997)
        with (
            patch.object(mac_budget, "pid_birth", return_value=None),
            patch.object(mac_budget, "group_alive", return_value=True),
        ):
            self.assertIsNone(self.budget.acquire(mac_budget.GIB, 1))
        with (
            patch.object(mac_budget, "pid_birth", return_value=None),
            patch.object(mac_budget, "group_alive", return_value=False),
        ):
            self.assertIsNotNone(self.budget.acquire(mac_budget.GIB, 1))

    def test_symlink_registry_is_rejected(self):
        target = self.root / "target"
        target.write_text("[]")
        (self.root / "leases.json").symlink_to(target)
        with self.assertRaises(ValueError):
            self.budget.status()
        self.assertEqual(target.read_text(), "[]")

    def test_cli_preserves_child_exit_code(self):
        config = self.root / "config.json"
        config.write_text(
            json.dumps(
                {
                    "memory_budget_gib": 8,
                    "io_slots": 1,
                    "headroom_gib": 0,
                    "disk_headroom_gib": 0,
                    "live_guard": False,
                }
            )
        )
        runner = Path(mac_budget.__file__)
        result = subprocess.run(
            [
                sys.executable,
                str(runner),
                "--state-dir",
                str(self.root / "state"),
                "--config",
                str(config),
                "run",
                "--memory-gib",
                "1",
                "--",
                sys.executable,
                "-c",
                "raise SystemExit(7)",
            ],
            capture_output=True,
        )
        self.assertEqual(result.returncode, 7, result.stderr.decode())

    def test_cli_wait_has_a_deadline(self):
        token = self.budget.acquire(8 * mac_budget.GIB, 1)
        with self.assertRaises(TimeoutError):
            self.budget.wait_for(mac_budget.GIB, 1, 0.04)
        self.budget.release(token)

    def test_nested_cli_reuses_parent_tree_reservation(self):
        config = self.root / "config.json"
        config.write_text(
            json.dumps(
                {
                    "memory_budget_gib": 1,
                    "io_slots": 1,
                    "headroom_gib": 0,
                    "disk_headroom_gib": 0,
                    "live_guard": False,
                }
            )
        )
        runner = str(Path(mac_budget.__file__))
        prefix = [
            sys.executable,
            runner,
            "--state-dir",
            str(self.root / "nested-state"),
            "--config",
            str(config),
            "run",
            "--memory-gib",
            "1",
            "--wait-seconds",
            "1",
            "--",
        ]
        result = subprocess.run(
            prefix + prefix + [sys.executable, "-c", "raise SystemExit(0)"],
            capture_output=True,
            timeout=5,
        )
        self.assertEqual(result.returncode, 0, result.stderr.decode())

    def test_nested_oversized_request_fails_without_waiting(self):
        config = self.root / "config.json"
        config.write_text(
            json.dumps(
                {
                    "memory_budget_gib": 4,
                    "io_slots": 1,
                    "headroom_gib": 0,
                    "disk_headroom_gib": 0,
                    "live_guard": False,
                }
            )
        )
        runner = str(Path(mac_budget.__file__))
        prefix = [
            sys.executable,
            runner,
            "--state-dir",
            str(self.root / "oversized-state"),
            "--config",
            str(config),
            "run",
        ]
        command = (
            prefix
            + ["--memory-gib", "1", "--"]
            + prefix
            + ["--memory-gib", "2", "--", sys.executable, "-c", "raise SystemExit(0)"]
        )
        result = subprocess.run(command, capture_output=True, timeout=5)
        self.assertEqual(result.returncode, 2, result.stderr.decode())
        self.assertIn(b"exceeds its parent", result.stderr)

    def test_process_group_is_held_after_direct_child_exit(self):
        config = self.root / "config.json"
        config.write_text(
            json.dumps(
                {
                    "memory_budget_gib": 1,
                    "io_slots": 1,
                    "headroom_gib": 0,
                    "disk_headroom_gib": 0,
                    "live_guard": False,
                }
            )
        )
        state = self.root / "group-state"
        marker = self.root / "started"
        code = 'import subprocess,sys; from pathlib import Path; subprocess.Popen([sys.executable,"-c","import time; time.sleep(.5)"]); Path(sys.argv[1]).touch()'
        process = subprocess.Popen(
            [
                sys.executable,
                str(Path(mac_budget.__file__)),
                "--state-dir",
                str(state),
                "--config",
                str(config),
                "run",
                "--memory-gib",
                "1",
                "--",
                sys.executable,
                "-c",
                code,
                str(marker),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        deadline = time.monotonic() + 3
        while not marker.exists() and time.monotonic() < deadline:
            time.sleep(0.02)
        self.assertTrue(marker.exists())
        self.assertEqual(
            mac_budget.Budget(
                state, mac_budget.Limits(mac_budget.GIB, 1, 0, 0, False)
            ).status()["reserved_io_slots"],
            1,
        )
        _, errors = process.communicate(timeout=5)
        self.assertEqual(process.returncode, 0, errors.decode())
        self.assertEqual(
            mac_budget.Budget(
                state, mac_budget.Limits(mac_budget.GIB, 1, 0, 0, False)
            ).status()["reserved_io_slots"],
            0,
        )


if __name__ == "__main__":
    unittest.main()

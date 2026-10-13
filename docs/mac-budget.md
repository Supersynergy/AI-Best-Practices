# Profiles, integration and recovery

The runner reserves declared whole-tree peak RAM and a number of I/O slots. This is admission control for cooperating future jobs. It cannot prevent an unregistered application or a misestimated job from allocating more memory or issuing writes.

The live Mac gate requires a normal native pressure level and sufficient estimated available memory for all existing reservations plus the new peak and headroom. The estimate includes free, inactive and speculative pages; these are not an allocation guarantee. Counting existing reservations is conservative and can count memory that has already been allocated twice. A minimum filesystem availability gate prevents admissions below the configured floor. GPU/model memory must be included in the declared peak.

## Conservative starting profiles

| Physical RAM | Reservation cap | Additional headroom | I/O slots |
|---|---:|---:|---:|
| 8–16 GiB | 2–4 GiB | 2–4 GiB | 1 |
| 24–32 GiB | 8–12 GiB | 6–8 GiB | 1 |
| 48–64 GiB | 16–24 GiB | 12–16 GiB | 1 |
| 128 GiB | 64 GiB | 24 GiB | 1 initially |

These are proposals to test, not vendor limits or verified optimums. Heavy jobs wait rather than displacing active work. Increase concurrency only after measuring the representative workload's time, pressure and recovery. Small cloud requests and simple read-only commands need not be treated as heavy local inference.

## Existing wrappers

An existing foreground wrapper can call:

```sh
mac-resource-run run --memory-gib 4 --io-slots 1 -- your-command
```

For background priority, retain the existing power/priority wrapper outside the runner. Update only the owned entry point; keep the original environment and exit status. Existing shells may need a fresh shell or explicit reload for a changed function definition. Do not restart active jobs to migrate them.

Nested calls inherit only a verified ancestor lease in the same registry. The parent's declaration must cover simultaneous children; inheritance does not allocate extra capacity. A nested request larger than the ancestor's declaration fails.

## State and failures

The default state lives in `~/Library/Caches/ai-best-practices/budget`, with private lock and registry files. There is no resident daemon. Admission checks poll only while waiting, with a deadline, and reuse a one-second live-probe result. A denied admission does not rewrite the registry every poll.

Only reservation metadata is stored, with no command arguments or credentials. Parent identity and process-group liveness prevent freeing capacity while owned work remains. Malformed registries fail closed and remain untouched. Inspect `mac-resource-run status` and the actual process tree before repairing state.

Foreground process groups are managed. Commands that independently detach into new sessions, resource use from external applications and hard kernel RAM/bandwidth caps are outside this implementation. Signals requested by the operator forward to the newly launched child group; the runner does not search for or terminate foreign jobs.

The runner does not change swap, create a RAM disk, move data, alter APFS reserves or delete backups. Its bookkeeping adds small admission/release writes; measure the full workload when comparing net I/O.

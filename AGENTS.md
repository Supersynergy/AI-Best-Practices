# AI Best Practices — repository contract

- Reuse the current objective, constraints, file ownership and executable acceptance. Preserve unrelated work.
- Text/path search starts with scoped `rg`/`rg --files`; Beads reads use native `bd` against the owning repository. Use `jq` for simple projections and Python for substantive structured processing or existing checks.
- Batch independent reads and reuse unchanged inputs. Serialize dependent steps and writes. Filter output before context; investigate after three failures at one blocker.
- Reproduce behavior-changing failures before the fix; preserve requested behavior, validation, errors and recovery. Run `just check` or `python3 -m unittest discover -s tests -v` after substantive code changes.
- New heavy Mac jobs should use the installed cooperative `mac-resource-run` with a declared whole-tree peak. Do not stop foreign jobs, disable swap or delete caches/data to make a metric green. Preserve durable checkpoints and required audit logs.
- Delegate only with independent ownership, relevant evidence, permission and resource/usage bounds. Never bypass a failed runtime guard or fall back to paid API transport automatically.
- Compare the same accepted workload, cache state and sample count; include latency, memory, write accounting, checking, retries and human rework. Missing metrics remain unknown. Publish only generic/sanitized evidence.
- Review contract, current diff and source-bound checks. Distinguish self/static review from an independent review and disclose remaining gates.
- Keep documentation readable. Do not introduce hooks, daemons, packages or model settings without a concrete consumer and verification.

## Code review rules

Flag early reservation release, PID-reuse mistakes, malformed-state overwrite, loss of child exit status, silent probe failures, unbounded waits, nested oversubscription, data-loss recommendations and unsupported SSD-life claims. Preserve active process groups when recovering stale owners. Documentation must state cooperative enforcement boundaries.

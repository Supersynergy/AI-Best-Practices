# Contributing

Start with a concrete failure or accepted workload. Include the expected and observed output, resource limits and executable check. Preserve other work and keep changes readable.

For performance changes, compare identical inputs and acceptance. Record cache state, sample count, wall time, peak memory, relevant write accounting, retries and recovery. State what remains unmeasured. Do not exchange durability or user effort for a better isolated number.

Run `just check` before submission. Keep runtime dependencies in the standard library unless the requirement warrants an audited dependency. Do not add a background monitor, automatic cleanup or a remote model call to the default path.

Never publish credentials, transcripts, machine identifiers or private filesystem paths. Findings from a static checker and an independent review must be identified separately.

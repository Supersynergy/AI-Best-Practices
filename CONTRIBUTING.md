# Contributing

Start with a concrete failure. For an improvement, define the accepted workload and the result that must stay unchanged. Include expected and observed output with the executable check. State resource limits. Preserve other work and keep changes readable.

For performance changes, compare identical inputs and acceptance. Record cache state, sample count, wall time, peak memory, relevant write accounting, retries and recovery. State what remains unmeasured. Do not exchange durability or user effort for a better isolated number.

Run `just check` before submission. Keep runtime dependencies in the standard library unless the requirement warrants an audited dependency. Do not add a background monitor, automatic cleanup or a remote model call to the default path.

Never publish credentials, transcripts, machine identifiers or private filesystem paths. Findings from a static checker and an independent review must be identified separately.

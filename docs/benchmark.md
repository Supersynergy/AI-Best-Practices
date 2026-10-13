# Executed benchmark

Three samples per arm on macOS, alternating arm order. Each arm starts three owned foreground jobs. Each job touches 32 MiB and writes one 1-MiB payload, with identical output hashes. Processes start fresh; filesystem cache is uncontrolled/warm. Device identifiers are omitted from the public record; this limits cross-machine comparisons.

| Metric (median) | Without admission | Shared I/O slot |
|---|---:|---:|
| Maximum active workers | 3 | 1 |
| Summed process footprint, including waiting wrappers | 125.20 MiB | 85.49 MiB |
| Total wall time | 0.704 s | 2.598 s |
| Logical payload bytes | 3145728 | 3145728 |

Admission reduced simultaneous demand and increased wall time. Total payload bytes did not decrease. This is a bounded synthetic comparison; it does not measure NAND write amplification or SSD life. No foreign job was stopped. The fixture uses a separate registry and a small declared budget; it does not reproduce every production application or the host's full configured headroom.

Runner SHA256: `bac9c22245ce081112078320322911ce550e6b4a0c9834bc7cb8482fac5e5e05`. [Raw measurements](benchmark.json).

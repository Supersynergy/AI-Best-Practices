# Executed benchmark

Three samples per arm on an M4 Max Mac, alternating arm order. Each arm starts three owned foreground jobs. Each job touches 32 MiB and writes one 1-MiB payload, with identical output hashes. Processes start fresh; filesystem cache is uncontrolled/warm.

| Metric (median) | Without admission | Shared I/O slot |
|---|---:|---:|
| Maximum active workers | 3 | 1 |
| Summed process footprint, including waiting wrappers | 123.69 MiB | 86.85 MiB |
| Total wall time | 0.735 s | 2.530 s |
| Logical payload bytes | 3145728 | 3145728 |

Admission reduced simultaneous demand and increased wall time. Total payload bytes did not decrease. This is a bounded synthetic comparison; it does not measure NAND write amplification or SSD life. No foreign job was stopped. The fixture uses a separate registry and a small declared budget; it does not reproduce every production application or the host's full configured headroom.

Runner SHA256: `2e0f1bba26ca8f14d0ce0c7b9e5bcd51dd52b2cafba5413240490182668530ff`. [Raw measurements](benchmark.json).

# Executed benchmark

Three samples per arm on an M4 Max Mac, alternating arm order. Each arm starts three owned foreground jobs. Each job touches 32 MiB and writes one 1-MiB payload, with identical output hashes. Processes start fresh; filesystem cache is uncontrolled/warm.

| Metric (median) | Without admission | Shared I/O slot |
|---|---:|---:|
| Maximum active workers | 3 | 1 |
| Summed process footprint, including waiting wrappers | 123.70 MiB | 87.36 MiB |
| Total wall time | 0.714 s | 2.560 s |
| Logical payload bytes | 3145728 | 3145728 |

Admission reduced simultaneous demand and increased wall time. Total payload bytes did not decrease. This is a bounded synthetic comparison; it does not measure NAND write amplification or SSD life. No foreign job was stopped. The fixture uses a separate registry and a small declared budget; it does not reproduce every production application or the host's full configured headroom.

Runner SHA256: `0903b7f50a07ffc33acde181712ae7863ae0fa10fd1518c0b90bf5ae747d039a`. [Raw measurements](benchmark.json).

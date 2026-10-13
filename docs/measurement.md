# Measure the same accepted work

Use a task record or benchmark artifact that already exists. Measurement should resolve a decision without becoming a larger workload than the improvement.

## Comparison sheet

| Field | Record |
|---|---|
| Outcome and acceptance | Exact inputs, preserved behavior and executable/user checks |
| Source and environment | Revision, relevant runtime/tool versions and owned boundaries |
| Workload | Representative task set, order and sample count |
| Cache state | Cold, warm or uncontrolled; process startup separately |
| Elapsed time | Request to acceptance; separate queue, execution and review |
| Human effort | Active minutes, decisions, interruptions and corrections |
| Reliability | Failed attempts, recovery, required review and acceptance rate |
| Resources | Peak footprint, pressure, I/O accounting and relevant concurrency |
| Usage and money | Provider-reported usage and actual charges, when available |
| Decision | Keep, revise or reject; unresolved risks and rollback |

Use medians and the range for small samples. Tail percentiles need enough observations to be useful; do not label a three-run maximum “p95.” Alternate comparison order where practical and keep workloads identical. Uncontrolled background activity stays a limitation, even when results look plausible.

## Keep metrics separate

Elapsed task time and active human effort have different units of meaning. Report them separately. Include review and rework in each applicable measure. Tool counts and token estimates help explain overhead; they do not establish savings or correctness.

For parallel work, measure the delivery’s actual start and end, the longest dependent path and each lane’s active effort. Overlapping durations cannot be summed into wall time. Higher throughput may coexist with worse individual latency. [SPACE: multiple dimensions](https://www.microsoft.com/en-us/research/publication/the-space-of-developer-productivity-theres-more-to-it-than-you-think/)

A useful success metric is accepted results per total effort for comparable tasks. Do not compare unlike tasks as if their value were identical. Track rejected or unfinished attempts so the denominator is not limited to successes.

## Check the size of the possible gain

If a measured stage contributes fraction `p` of sequential runtime and becomes `s` times faster, the ideal end-to-end speedup is `1 / ((1 - p) + p / s)`. This assumes the rest stays unchanged and ignores new overhead. Eliminating a 10% stage can improve the whole path by at most about 1.11× under those assumptions. Rework and queueing may violate the assumptions; measure the complete result.

For repeated human friction, use `saved delay × observed frequency × affected people` as a planning estimate. Keep confirmation, undo, permissions and recovery intact. Do not present projected annual savings as executed evidence.

## Resource comparisons

Measure bounded RAM buffers against pressure, paging and latency. Compare logical file bytes, host device writes and endurance indicators on their own measurement layers. Preserve required persistence and checkpoints. A lower peak process footprint or an idle swap-used total does not prove fewer NAND writes. [Storage boundaries](storage.md)

The included [benchmark](benchmark.md) records a concurrency/memory/latency tradeoff. It is not an evaluation of the entire handbook or a universal productivity score.

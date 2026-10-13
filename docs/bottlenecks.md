# Find the development bottleneck

This is a diagnostic map, not a universal ranking. A team may spend more time waiting for decisions or review than compiling code. Trace a representative task from request to accepted delivery before optimizing one stage. Include work that happens outside the editor.

| Constraint | Observable signal | First measurement | Small practical response | Common mistake |
|---|---|---|---|---|
| Unclear requirements | Repeated questions or rejected changes | Changes in acceptance; rework minutes | One result, preserved behavior and representative input | Generating a large feature before agreeing on success |
| Missing context | Repeated scans; wrong caller or revision | Repeated inputs; time to decisive evidence | Exact local query and a small source-bound task record | Loading every document into the prompt |
| Slow build/test feedback | Long waits after each edit | Check duration, queue time, cache hits | Existing incremental checks; retain final integration gates | Clearing caches or adding workers without timing |
| Unreliable tests | Intermittent failures | Failure input, order, state and reproducibility | Isolate state and repair the signal | Retrying until green or hiding the failure |
| Review/integration queues | Finished branches waiting | Age of waiting changes; review and merge time | Smaller complete changes and explicit ownership | Counting generated code as delivered work |
| Too much work in progress | Many open tasks; slow finishes | Task age, blockers and completed results | Finish the priority constraint before admitting more work | Maximizing agent count or utilization |
| Process and network overhead | Short jobs dominated by startup or RTT | Initialization and transfer time | Batch reads; reuse a worker only past its measured break-even | Introducing a resident service for one request |
| CPU, RAM or I/O contention | More workers worsen latency | Throughput, tail latency, pressure and write deltas | Shared admission and measured concurrency | Assigning a full-machine budget to every job |
| Dependency/environment drift | Local green; installed or CI failure | Revision, runtime, lockfile and artifact identity | Reproducible setup and boundary-specific probes | Assuming a source check proves installed behavior |
| User interaction friction | Re-entry, backtracking or abandonment | Success rate, steps, decisions and recovery | Useful defaults, direct actions and reversible changes | Faster feedback that conceals a failed save |
| Agent/tool mismatch | Repeated irrelevant results | Acceptance rate, correction effort and failed calls | Exact task context and the cheapest fitting tool | Comparing model labels instead of accepted tasks |
| Recovery and security gaps | Lost progress or unbounded retries | Failed dependency/cancellation behavior; recovery time | Durable state, bounded retries and safe rollback | Trading recoverability for a faster benchmark |

The map combines engineering diagnosis with published guidance. [DORA CI](https://dora.dev/capabilities/continuous-integration/) supports short, reliable feedback. [DORA work-in-process limits](https://dora.dev/capabilities/wip-limits/) addresses waiting work and hidden constraints. [SPACE](https://www.microsoft.com/en-us/research/publication/the-space-of-developer-productivity-theres-more-to-it-than-you-think/) explains why one activity metric cannot represent productivity. The remedies above remain choices to verify on the actual workload.

## Choose the next intervention

Capture a baseline for one accepted result. Identify the largest avoidable delay or recurring human burden. Choose the smallest reversible intervention and compare the same acceptance afterward. Record failures and rollback cost, then keep, revise or reject the change.

Distinguish task latency from throughput. Three jobs finishing over an hour can be valuable while a single task still waits too long. Parallel task durations overlap, so adding them does not yield wall-clock time. An agent’s inter-tool gap also includes orchestration and waiting; it does not expose private reasoning or measure reasoning time.

For recurring friction, estimate saved time as `delay saved × occurrences × affected people`. Record the observed frequency and separate projections from measured savings. This helps compare repeated small delays with an occasional large one without imposing universal thresholds.

## Interpret AI evidence carefully

METR’s July 2025 study observed a 19% slowdown for 16 experienced contributors completing 246 tasks with early-2025 tools on familiar repositories. Its authors limit the claim to that setting. [Original study](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/)

The February 2026 update reports serious selection effects and difficulty measuring time when developers use agents concurrently. The authors call the new estimate an unreliable signal of current productivity. Neither result establishes a fixed speedup or slowdown for present Codex work. Measure representative accepted tasks, including human effort and quality. [Updated study design](https://metr.org/blog/2026-02-24-uplift-update/)

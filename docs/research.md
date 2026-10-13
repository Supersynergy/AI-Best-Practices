# Research execution and limits

Superweb and GH Max were both executed for this project with bounded result counts and raw evidence kept outside the public repository.

- Superweb search returned results, including irrelevant homonyms. They were rejected rather than treated as evidence. Three official-page fetches failed at its egress preflight. The installed CLI's failure did not establish a general Internet outage; primary OpenAI pages were verified through a separate browsing tool.
- GH Max returned an official `openai/codex/docs/agents_md.md` hit among unrelated repositories. The repository filter was not treated as an absolute guarantee. The official hit was verified through GitHub's contents API; private caches and raw results were not published.
- A requested research-agent start used an isolated registered capsule. The existing runtime guard rejected the encrypted tool input because it lacked a verifiable plaintext/content binding. The guard was preserved. No child agent was started, and research continued in the parent session.
- Native root filesystem tracing was unavailable without authentication. Read-only process counters and block-driver deltas provided partial write attribution, with explicit gaps for unreadable and short-lived processes.

The software is an experimental public candidate. Local tests and static review do not substitute for an independent review. No SSD-life extension, paid provider savings or universal Mac optimum is claimed.

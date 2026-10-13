# Primary-source ledger

Checked on 2026-10-13. Guidance below is paraphrased; examples and implementation are original. A cited design principle does not prove a local performance gain.

| Source | What it supports |
|---|---|
| [OpenAI: AGENTS.md](https://developers.openai.com/codex/guides/agents-md/) | Global/project discovery, override precedence and loading verification. Redirects to ChatGPT Learn. |
| [OpenAI: prompting](https://developers.openai.com/codex/prompting/) | Concrete task context, bug reproduction and relevant verification. |
| [OpenAI: worktrees](https://developers.openai.com/codex/app/worktrees/) | Separate checkouts for independent parallel work, with shared Git metadata. |
| [openai/codex: agents_md.md](https://github.com/openai/codex/blob/main/docs/agents_md.md) | Official upstream document discovered through GH Max and checked through GitHub's contents API. Blob `4fa02abd1d78a779dc8b6295e69429bcb5d7a129` at discovery. |
| [Apple: memory usage](https://support.apple.com/guide/activity-monitor/view-memory-usage-actmntr1004/mac) | Pressure, compression, file caches and swap-used interpretation. |
| [Apple: reducing disk writes](https://developer.apple.com/documentation/xcode/reducing-disk-writes) | Temporary RAM caches and reduced/batched persistence. |
| [Apple: minimize I/O](https://developer.apple.com/library/archive/documentation/Performance/Conceptual/power_efficiency_guidelines_osx/MinimizingIO.html) | Reuse system caching, avoid unnecessary repeated writes and profile actual I/O. Archived guidance. |
| [Apple: APFS volumes](https://support.apple.com/guide/disk-utility/add-delete-or-erase-apfs-volumes-dskua9e6a110/mac) | Shared container space and reserve/quota concepts. The host's `diskutil` manual additionally defines reserve guarantees. |
| [Kingston: over-provisioning](https://www.kingston.com/en/blog/pc-performance/overprovisioning) | General NAND maintenance and write amplification; no Apple-specific endurance guarantee. |
| [GitHub: Actions billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions) | Standard hosted runners for public repositories are free. This workflow uses no larger runner or artifact/cache upload. |

The native Mac binding layout was checked against the installed Apple SDK's `sys/resource.h` (`rusage_info_v4`) and `libproc.h` (`proc_pid_rusage`). This project's tests and benchmark are implementation evidence, separate from these sources.

# Daily development workflows

Use one workflow for the actual task. Scale checks with behavior, risk and project requirements. Keep the [principles](principles.md) as a reference rather than loading all of them into every agent request.

## Fix a behavior bug

1. Inspect the current task, owner, source state and actual failing input.
2. Find the affected code and callers with a scoped query. Record expected and observed output.
3. Observe the relevant regression fail for the intended reason.
4. Fix the shared cause with the smallest complete change.
5. Run the regression and affected checks, then required integration checks.
6. Verify the actual runtime boundary and obtain required review of the current diff.
7. Return executed evidence and any remaining gap. Stop when acceptance passes.

If repeated attempts fail at the same prerequisite, investigate it. A missing service or login is not fixed by changing unrelated code.

## Deliver a feature

Start with one useful user scenario, its constraints and a current baseline. Implement a complete slice through the affected callers, persistence and interface. Reuse established patterns. Check the normal path and relevant empty/error/recovery states. Exercise the real route when the interface changes, including focus and reload behavior. Integrate with required review before treating the feature as delivered.

## Improve performance

Write the accepted workload and preservation constraints first. Time the end-to-end path and isolate the dominant avoidable cost. Decide whether to remove work, reshape a boundary, improve an algorithm, reuse a valid result or batch independent work. Measure the same workload afterward, including failed runs and recovery. Reject an intervention that speeds one stage while increasing total effort or breaking outputs.

Use the [measurement sheet](measurement.md). Cold startup, repeated warm use and batch throughput answer different questions.

## Reduce interaction friction

Select a frequent task with a real success event. Record intent, first useful feedback, durable completion, steps and interruptions. Reduce repeated input or unnecessary navigation with contextual defaults, direct actions or a shortcut. For reversible operations, offer effective undo where appropriate. Preserve explicit authority for irreversible actions. Confirm completion and recovery; a quick optimistic state is not evidence that persistence succeeded.

## Work in parallel

Choose independent lanes from the dependency graph. Give each one exclusive writes, a source revision, a compact task contract and its check. Reserve shared host capacity and keep a single integration owner. Return artifact references and decisive results rather than full transcripts. Wait on the tool’s completion mechanism when available. Review the integrated state after merging; separate green branches are insufficient.

Keep one lane when startup, coordination and review exceed the parallel benefit. Never bypass a runtime guard or consume unapproved capacity to make delegation happen. [OpenAI: worktrees](https://developers.openai.com/codex/app/worktrees/)

## Resume or hand off

Record the outcome, current revision, owned files, checks already executed, unresolved blocker and next command in the existing task artifact. Include an evidence reference and recovery boundary. On return, recheck state that could have changed. Avoid rerunning successful checks unless new edits, failures or relevant uncertainty invalidate them.

# Read storage numbers at the right layer

APFS volumes share a container. A reserve guarantees minimum storage for a volume; a quota limits its growth. These settings change the interpretation of per-volume capacity. [Apple: APFS volumes](https://support.apple.com/guide/disk-utility/add-delete-or-erase-apfs-volumes-dskua9e6a110/mac)

Use a bounded read-only snapshot:

```sh
df -k /System/Volumes/Data
diskutil apfs list
diskutil info /System/Volumes/Data
sysctl vm.swapusage
vm_stat
```

Inspect every volume's allocation, reserve and quota, then compare with the filesystem's `statvfs` total and available bytes. Do not equate `df`'s per-volume percentage with NAND wear or silently discard disagreeing values. Reservations, other volumes, reclaimability, delayed accounting and concurrent activity can matter; establish the actual cause for that host.

In the motivating Mac case, the difference between container capacity and filesystem total matched an additional volume's 500-GB reserve exactly. That other volume also consumed substantial storage. The container's zero-free report and positive filesystem availability remained different API views; the reserve was preserved and the remaining free-counter semantics were not proven as a universal APFS formula. Values changed during other concurrent activity.

For writes, record deltas over a bounded interval. Sample short-lived processes when possible. Permissions may leave some processes and kernel I/O unattributed. A short burst is not a daily forecast. Preserve private paths and identifiers in local evidence rather than publishing them.

Host byte counters measure traffic observed at their layer. NAND write amplification and remaining endurance require suitable device telemetry; a normal SMART status alone is insufficient. [Kingston: over-provisioning and amplification](https://www.kingston.com/en/blog/pc-performance/overprovisioning)

Before changing storage layout or deleting a backup, prepare a concrete inventory and recovery plan under the owner's authority. This project's diagnostics and runner perform neither action.

# archive_snapshot
Move btrfs snapshots to other disks automatically

Created in a ritalinless fog to free up space on my VM images SSD by sending my nightly snapshots (done via cron) to whatever disk has the most space free and isn't on the deny list.

Very dirty and not good. I don't code often enough. Fuck me.

## Todo
* Verify transfers actually worked (inside the script, not manually outside afterward)
* Maybe command line options
* Learn to code
* Make coffee
* Batching: If we're reading from a fast SSD but writing to slow HDDs, maybe we can run multiple subprocesses to write a snapshot to each to make clearing faster.
* Make sure there's actually space on (any of) the target volume(s).

# archive_snapshot
Move btrfs snapshots to other disks automatically

Created in a ritalinless fog to free up space on my VM images SSD by sending my nightly snapshots (done via cron) to whatever disk has the most space free and isn't on the deny list.

Very dirty and not good. I don't code often enough. Fuck me.

## Usage
In my use case I have
* an Unraid server with the standard Unraid array (a bunch of indiviual SATA HDDS, formatted btrfs, mounted under Limetech's weird scheme)
* a caching SATA SSD array (irrelevant here)
* a NVMe SSD for VM images (btrfs, mounted on /mnt/images)

To make this work I created a subvolume called "domains" on /mnt/images, and a snapshot subvolume unimaginitvely called ".snapshots". Every night a cron job is called to create a readonly snapshot of my VM images.
```
0 2 * * * btrfs subvolume snapshot -r /mnt/images/domains /mnt/images/.snapshots/`date +%Y%m%d`
```
This tool will check all potentially viable mounts (in this scenario, anything /dev/md* thats btrfs and mounted rw and not on the deny list. It should then determine which disk has the most free space and migrate the snapshot over via btrfs send (via subprocess)

There's not a lot of error checking, and it's pretty tailored to my specific use case. Then again, I don't think anybody but me will probably ever use this so... \*shrug\*?

Configuration is minimal and set via variables near the top of the file. 

## Todo
* Verify transfers actually worked (inside the script, not manually outside afterward)
* Maybe command line options
* Learn to code
* Make coffee
* Batching: If we're reading from a fast SSD but writing to slow HDDs, maybe we can run multiple subprocesses to write a snapshot to each to make clearing faster.
* Make sure there's actually space on (any of) the target volume(s).
* Improve speed measurement
* Check to see if the snapshot we're sending already exists in some form on another disk, if there's room to continue, and do that, instead of potentially duplicating snapshots or partial snapshots across multiple disks. This *shouldn't* be an issue though, as snapshots *should* be removed after they're sent. But if they're interrupted, maybe?

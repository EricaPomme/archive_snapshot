import os
import subprocess
import re
import time

### Configuration settings
PATH_BTRFS = '/sbin/btrfs'
PATH_SNAPSHOT_SOURCE = '/mnt/images/.snapshots' # Path to the source snapshots
SUBPATH_SNAPSHOT_TARGET = '.snapshots' # The non-changing part of the target path, e.g.: '.snapshots'. Don't prefix with disk path.
DISK_TARGET_DENYLIST = [] # Don't put snapshots on these mounts. e.g.: ['/mnt/disk4', '/mnt/disk3']
REGEX_MOUNTPOINT = '^/dev/md[0-9]+ on /mnt/disk[0-9]* type btrfs \(rw' # Unraid. Adjust if you're using a different distro.

## Validate configuration entries
if not os.path.isdir(PATH_SNAPSHOT_SOURCE):
    raise Exception(f'Invalid configuration: PATH_SNAPSHOT_SOURCE is not a directory.')
for entry in DISK_TARGET_DENYLIST:
    if re.match('^/mnt/disk[0-9]+$', entry) is None:
        raise ValueError(f'Invalid disk target denylist entry: {entry}')

# Get potential target volumes 
targets = []
for mount in subprocess.check_output(['/bin/mount']).decode('utf-8').split('\n'):
    if re.match(REGEX_MOUNTPOINT, mount) is not None:
        mount = mount.split(' on ')[1]
        mount = mount.split(' type ')[0]
        if mount not in DISK_TARGET_DENYLIST:
            targets.append(mount)

def get_snapshot_size(path: str) -> int:
    count = 0
    for r, _, f in os.walk(path):
        for i in f:
            count += os.path.getsize(os.path.join(r, i))
    return count

def get_most_free() -> str:
    disks = {}
    for target in targets:
        disks[target] = subprocess.check_output(['/bin/df', target]).decode('utf-8').split('\n')[1].split()[3]
    return max(disks, key=disks.get)

# Main routine
for snapshot in os.listdir(PATH_SNAPSHOT_SOURCE):
    # Targets
    src_path = os.path.join(PATH_SNAPSHOT_SOURCE, snapshot)
    target_disk = get_most_free()
    dst_path = os.path.join(target_disk, SUBPATH_SNAPSHOT_TARGET)

    # Create snapshot target directory if it doesn't exist
    out = subprocess.check_output([PATH_BTRFS, 'subvolume', 'list', target_disk]).decode('utf-8').split('\n')
    out = [i for i in out if re.match(f"ID \d+ gen \d+ top level \d+ path {SUBPATH_SNAPSHOT_TARGET}", i) is not None]
    if len(out) > 0:
        print(f"Valid snapshot path on {target_disk}: {out[0]}. {len(out)-1} snapshots on this disk.")
    else:
        print(f"No snapshot path found on {target_disk}. Creating {dst_path}.")
        subprocess.check_output([PATH_BTRFS, 'subvolume', 'create', dst_path])

    # Counters
    src_size = get_snapshot_size(src_path)
    dst_size_initial = get_snapshot_size(dst_path) # for calculating speed, if we don't start from zero
    start_time = time.time()

    # Move snapshot to target
    print(f"Moving snapshot {src_path} -> {target_disk}.")
    src = subprocess.Popen([PATH_BTRFS, 'send', src_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    dst = subprocess.Popen([PATH_BTRFS, 'receive', dst_path], stdin=src.stdout, stderr=subprocess.PIPE)
    while (src.returncode is None and dst.returncode is None):
        dst_size = get_snapshot_size(dst_path)
        speed = (dst_size - dst_size_initial) / (time.time() - start_time) / 1048576
        h, r = divmod(time.time() - start_time, 3600)
        m, s = divmod(r, 60)
        h, m, s = int(h), int(m), int(s)
        if m < 10:
            m = f"0{m}"
        if s < 10:
            s = f"0{s}"
        print(f"{snapshot}: {dst_size/1048576:,.2f}/{src_size/1048576:,.2f}MB | {dst_size*100/src_size:.2f}% @ {speed:.2f}MB/s | {h}:{m}:{s} elapsed.")
        time.sleep(5)
        src.poll()
        dst.poll()
    print()

    # Remove snapshot from source if src and dst are 0
    if src.returncode == 0 and dst.returncode == 0:
        print(f"Removing snapshot {src_path}.")
        subprocess.run([PATH_BTRFS, 'subvolume', 'delete', src_path])
    

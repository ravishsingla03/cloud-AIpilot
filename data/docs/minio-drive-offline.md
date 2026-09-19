# MinIO: drive offline in an erasure set

## Symptom

The MinIO console or `mc admin info` shows fewer online drives than
expected. Reads and writes continue while enough drives survive, because
erasure coding tolerates the loss of up to the parity count in each set.
Quietly running below parity is the dangerous state: the next failure
takes the erasure set read-only or offline.

## How much loss the deployment tolerates

With the default EC:4 scheme on a 16-drive set, 12 data and 4 parity
shards exist per object. Reads succeed while at least 12 drives in the
set are online, writes require a quorum that includes parity, so write
quorum is lost before read quorum. The tolerance is per erasure set, not
per cluster: four dead drives in one set is fatal even if every other
set is complete.

## Cause: the filesystem went read-only

A drive whose XFS filesystem flipped to read-only after an IO error
still mounts and still appears in the OS, but MinIO marks it offline.
Check dmesg for IO errors and for the remount. Replacing a healthy disk
because of a transient controller error is a common and expensive
mistake.

## Cause: wrong permissions or missing format.json

After a node rebuild, drives mounted at the right path but owned by the
wrong user, or wiped of their `.minio.sys/format.json`, are rejected.
MinIO refuses to assume an empty drive belongs to the set; healing it
back in is a deliberate action.

## Healing a replaced drive

Replace the disk, mount it at the same path with the same ownership,
and let MinIO detect it. `mc admin heal -r` reports progress; healing
reads from the surviving shards and rebuilds the missing ones, so it is
bounded by network and disk throughput of the whole set, not of the new
drive alone.

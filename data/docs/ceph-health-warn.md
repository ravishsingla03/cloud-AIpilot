# Ceph: cluster reports HEALTH_WARN

## Symptom

`ceph status` reports HEALTH_WARN with one or more warning codes. The
cluster is still serving IO in most warning states, which is exactly why
these get ignored until they become HEALTH_ERR. Read the detail output
with `ceph health detail` before touching anything; the summary line
hides which pool or OSD is involved.

## PGs stuck in degraded or undersized

Degraded means some objects have fewer replicas than the pool size.
Undersized means the placement group has fewer OSDs assigned than the
pool size requires. Both usually follow an OSD going down. If recovery
is progressing, the counts fall over time and no action is needed. If
they are frozen, the CRUSH rule cannot find a placement target, often
because a whole failure domain is offline.

## PGs stuck inactive or peering

Inactive PGs block client IO on the affected pool. Peering that never
completes usually means one OSD in the acting set is unreachable, a
network partition between the public and cluster networks, or an OSD
that is up in the map but not actually responding. Query the PG with
`ceph pg <pgid> query` and look at the peers it is waiting on.

## OSD nearfull and backfillfull

Ceph raises nearfull at 85 percent and stops backfill at 90 percent by
default. A single nearfull OSD in an otherwise empty cluster means the
data distribution is skewed, not that the cluster is out of space. The
balancer module or a reweight fixes distribution; adding capacity is the
answer only when the cluster as a whole is full.

## Clock skew and monitor quorum

Monitors report clock skew when their times drift by more than 50
milliseconds. Skew large enough to break quorum takes the whole cluster
offline even though every OSD is healthy. Fix NTP on the monitor hosts
rather than raising the tolerance.

# Kubernetes: Pod stuck in Pending

## Symptom

The pod exists in the API but no node has accepted it. Pending means the
scheduler has not placed it, or it was placed and the kubelet cannot
start it yet. `kubectl describe pod` and the FailedScheduling event tell
you which of the two it is, and the event message names the constraint
that could not be satisfied.

## Cause: insufficient CPU or memory

The message reads Insufficient cpu or Insufficient memory followed by
the number of nodes that were rejected. The scheduler compares the pod's
requests, not its limits, against the allocatable capacity of each node.
A cluster that looks half idle in a dashboard can still be unschedulable
because requests are reserved whether or not they are used.

## Cause: node selector or affinity mismatch

If the pod carries a nodeSelector or a required node affinity rule and
no node has the matching label, the scheduler reports that zero of N
nodes matched the selector. This is common after a node pool is replaced
and the new nodes are created without the old labels.

## Cause: taints without matching tolerations

Nodes that are cordoned, under disk pressure, or dedicated to a
workload carry taints. A pod without the matching toleration is never
scheduled on them. The event lists the taint that blocked placement,
for example node.kubernetes.io/not-ready or a custom dedicated taint.

## Cause: unbound PersistentVolumeClaim

If the pod mounts a PVC that is still Pending, the pod stays Pending as
well. Usually the StorageClass does not exist, the provisioner is down,
or the requested access mode cannot be satisfied by the backing storage.
Describe the PVC, not the pod, to see the provisioner's error.
